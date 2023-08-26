# -*- coding: latin-1 -*-
# Copyright (c) 2023, pibiCo and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from frappe.contacts.doctype.contact.contact import Contact
from frappe.utils.background_jobs import enqueue
import os
import uuid
from frappe import _
from frappe.utils import get_files_path, get_url, random_string

from PIL import Image
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import SquareModuleDrawer, GappedSquareModuleDrawer, HorizontalBarsDrawer, RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask

import base64
from io import BytesIO

import requests
from requests.auth import HTTPBasicAuth
import vobject

import re
import json
import html

from datetime import datetime

# Fetch CardDAV details
url = frappe.conf.get('carddav')
username = frappe.conf.get('carduser')
password = frappe.conf.get('cardkey')

class CustomContact(Contact):
  """
    Inherit contact and extend it.
  """
  def after_insert(self):
    # Skip execution if the contact is being created from a VCF file
    if self.flags.get('from_vcf'):
      return

@frappe.whitelist()
def enqueue_upload_vcards_to_carddav(contact_names):
  # Convert the received JSON string back into a Python list
  contact_names = json.loads(contact_names)

  # Start a new background job and return its ID
  job = enqueue(
    upload_vcards_to_carddav,
    queue='long',
    timeout=14400,
    is_async=True,
    job_name="Upload vCard to CardDAV server",
    contact_names=contact_names)
  return job.id

def upload_vcards_to_carddav(contact_names):
  total_contacts = len(contact_names)

  for i, contact_name in enumerate(contact_names, 1):
    contact = frappe.get_doc("Contact", contact_name)

    # If vcard_string is empty, generate it with build_vcard method
    if not contact.cr_vcard_text:
      contact.cr_vcard_text = build_vcard(contact_name)

    upload_vcard_to_carddav(
      contact.cr_vcard_text
    )
    # Calculate progress percentage and publish realtime
    progress = (i / total_contacts) * 100
    frappe.publish_realtime('upload_vcards_progress', {'progress': progress, 'name': contact_name}, user=frappe.session.user)

@frappe.whitelist()
def build_vcard(contact_name):
  # With the data of a Frappe contact, build a vCard in version 3.0
  c = frappe.get_doc('Contact', contact_name)

  vcard = ['BEGIN:VCARD', 'VERSION:3.0']
  txt = "PRODID:-//{}".format('pibifeed')

  vcard.append(txt)

  if not c.cr_vcard_text is None:
    existing = vobject.readOne(c.cr_vcard_text)
    uid = existing.uid.value
  else: 
    uid = uuid.uuid4().hex
  
  txt = "UID:{}".format(uid)
  vcard.append(txt)

  txt = "N:{};{};{};{};".format(nn(c.last_name), nn(c.first_name), nn(c.middle_name), nn(c.salutation))
  vcard.append(txt)

  txt = "FN:{}".format(c.name)
  vcard.append(txt)

  if c.designation:
    txt = 'TITLE:{}'.format(c.designation)
    vcard.append(txt)
  if c.company_name:
    txt = 'ORG:{}'.format(c.company_name)
    if c.department:
      txt += ';{}'.format(c.department)
    vcard.append(txt)

  if c.gender:
    txt = "X-GENDER:{}".format(c.gender)
    vcard.append(txt)

  if c.image and c.image.startswith('/files/'):
    urlphoto = frappe.utils.get_url() + c.image
    txt = "PHOTO;TYPE=JPEG;ENCODING=BASE64:{}".format(urlphoto)
    vcard.append(txt)

  if c.address:
    add = frappe.get_doc('Address', c.address)
    txt = 'ADR:;;{};{};{};{};{}'.format(nn(add.address_line1), nn(add.city),
                                        nn(add.state), nn(add.pincode), nn(add.country))
    vcard.append(txt)

  if c.email_id:
    txt = 'EMAIL;TYPE=INTERNET:{}'.format(c.email_id)
    vcard.append(txt)

  if c.phone:
    txt = 'TEL;TYPE=VOICE,WORK:{}'.format(c.phone)
    vcard.append(txt)
  if c.mobile_no:
    txt = 'TEL;TYPE=VOICE,CELL:{}'.format(c.mobile_no)
    vcard.append(txt)

  # Add Notes and Website (URL) either in pibiAID or pibiCARD
  if hasattr(c, 'ai_notes') and c.ai_notes:
    txt = 'NOTE:{}'.format(c.ai_notes.replace('\n', ' ').replace('\r', ''))
    vcard.append(txt)
  if hasattr(c, 'cr_notes') and c.cr_notes:
    txt = 'NOTE:{}'.format(c.cr_notes.replace('\n', ' ').replace('\r', ''))
    vcard.append(txt)

  if hasattr(c, 'ai_web_site') and c.ai_web_site:
    txt = 'URL:{}'.format(c.ai_web_site)
    vcard.append(txt)
  if hasattr(c, 'cr_web_site') and c.cr_web_site:
    txt = 'URL:{}'.format(c.cr_web_site)
    vcard.append(txt)  

  datetime = c.modified.strftime("%Y%m%dT%H%M%SZ")
  txt = 'REV:{}'.format(datetime)
  vcard.append(txt)

  vcard.append('END:VCARD')
  c.cr_vcard_text = '\n'.join(vcard)
  c.save()

  return '\n'.join(vcard)

def nn(value):
    return value or ''

@frappe.whitelist()
def get_qrcode(input_data, logo):
  qr = qrcode.QRCode(
        version=1,
        box_size=6,
        border=1
  )
  qr.add_data(input_data)
  qr.make(fit=True)
  path = frappe.utils.get_bench_path()
  site_name = frappe.utils.get_url().replace("http://","").replace("https://","")
  if ":" in site_name:
    pos = site_name.find(":")
    site_name = site_name[:pos]

  if logo:
    if not 'private' in logo:
      embedded_image_path = os.path.join(path, "sites", site_name, 'public', logo[1:])
    else:
      embedded_image_path = os.path.join(path, "sites", site_name, logo[1:])

    with Image.open(embedded_image_path) as embed_img:
      embedded = embed_img.copy()

  else:
    embedded = None

  if embedded:
    img = qr.make_image(image_factory=StyledPilImage, color_mask=RadialGradiantColorMask(back_color=(255, 255, 255), center_color=(70, 130, 180), edge_color=(34, 34, 34)), module_drawer=RoundedModuleDrawer(), eye_drawer=SquareModuleDrawer(), embeded_image=embedded)
  else:
    img = qr.make_image(image_factory=StyledPilImage, color_mask=RadialGradiantColorMask(back_color=(255, 255, 255), center_color=(70, 130, 180), edge_color=(34, 34, 34)), module_drawer=RoundedModuleDrawer(), eye_drawer=SquareModuleDrawer())

  temp = BytesIO()
  img.save(temp, "PNG")
  temp.seek(0)
  b64 = base64.b64encode(temp.read())
  return "data:image/png;base64,{0}".format(b64.decode("utf-8"))

@frappe.whitelist()
def get_site_config_values(keys):
  keys = keys.split(',')  # Convert the comma-separated string to a list
  values = {}
  for key in keys:
    values[key] = frappe.conf.get(key)
  return values

@frappe.whitelist()
def upload_vcard_to_carddav(vcard_string):
  # Parse the vCard string into a vobject
  vcard = vobject.readOne(vcard_string)
  # Get the vCard UID
  uid = vcard.uid.value
  if '-' in uid:
    frappe.msgprint(_("vCards must be generated in Frappe to get synchronized"))
    frappe.msgprint(vcard_string)
    return
    
  vcard_url = f"{url}/{uid}.vcf"
  # Check if vCard exists
  response = requests.get(vcard_url, auth=HTTPBasicAuth(username, password))
  
  if response.status_code in [200, 404]:
    response = requests.put(vcard_url, data=vcard_string, headers={"Content-Type": "text/vcard"}, auth=HTTPBasicAuth(username, password))
    frappe.msgprint(f"vCard for {uid} created/updated successfully {response.status_code}")
  else:
    frappe.msgprint(f"vCard for {uid}: {response.status_code} {response.text}")

@frappe.whitelist()
def create_contacts_from_vcf(vcf_content):
  try:
    # Parse the VCF content using vobject
    contact_names = []
    total_contacts = sum(1 for _ in vobject.readComponents(vcf_content))  # Calculate total contacts

    for i, vcard in enumerate(vobject.readComponents(vcf_content)):
      try:
        # Extract the first_name and last_name from the vCard
        if hasattr(vcard, "n"):
          first_name = vcard.n.value.given if hasattr(vcard.n.value, "given") else ""
          last_name = vcard.n.value.family if hasattr(vcard.n.value, "family") else ""
        else:
          if hasattr(vcard, "fn"):
            first_name = vcard.fn.value if hasattr(vcard, "fn") else ""
            last_name = ""
          else:
            first_name = "Contact"
            last_name = "No Name"

        #full_name = f"{first_name} {last_name}".strip()
        if hasattr(vcard, "fn"):
          full_name = vcard.fn.value if hasattr(vcard, "fn") else "Contact No Name"
            
        # Create a new Contact in Frappe using the extracted information
        new_contact = frappe.get_doc({
          'doctype': 'Contact',
          'first_name': first_name,
          'last_name': last_name,
          'phone_nos': [],
          'email_ids': [],
          'company_name': vcard.org.value[0] if hasattr(vcard, "org") else "",
          'department': vcard.org.value[1] if hasattr(vcard, "org") and len(vcard.org.value) > 1 else "",
          'designation': vcard.title.value if hasattr(vcard, "title") else "",
        })

        # Set custom fields for URL and NOTE if they exist
        # Extract NOTE and URL
        note_value = vcard.note.value if hasattr(vcard, "note") else ""
        url_value = vcard.url.value if hasattr(vcard, "url") else ""
        if url_value and 'ai_web_site' in new_contact.as_dict():
          new_contact.ai_web_site = url_value
        elif url_value and 'cr_web_site' in new_contact.as_dict(): # Only if ai_web_site wasn't set
          new_contact.cr_web_site = url_value
        
        if note_value and 'ai_notes' in new_contact.as_dict():
          new_contact.ai_notes = note_value
        elif note_value and 'cr_notes' in new_contact.as_dict(): # Only if ai_notes wasn't set
          new_contact.cr_notes = note_value

        email_value = vcard.email.value if hasattr(vcard, "email") else None

        if email_value:
          new_contact.append('email_ids', {
            'doctype': 'Contact Email',
            'email_id': email_value,
            'is_primary': 1
          })

        # Handling for phone numbers
        if hasattr(vcard, "tel"):
          for tel in vcard.tel_list:
            phone_number = re.sub(r'\D', '', tel.value) if tel.value else ""
            new_contact.append('phone_nos', {
              'doctype': 'Contact Phone',
              'phone': phone_number
            })
        else:
          for key in vcard.contents:
            if key.startswith('item') and key.endswith('.TEL'):
              phone_number = re.sub(r'\D', '', vcard.contents[key][0].value) if vcard.contents[key][0].value else ""
              new_contact.append('phone_nos', {
                'doctype': 'Contact Phone',
                'phone': phone_number
              })
            
        # Generate the full_name
        new_contact.full_name = full_name
        new_contact.cr_vcard_text = vcard.serialize()

        existing_contact = frappe.db.exists("Contact", {"full_name": full_name}) if full_name else None
        if existing_contact:
          continue
        else:
          # Save the new contact
          new_contact.flags.from_vcf = True
          new_contact.insert(ignore_permissions=True)
          contact_names.append(new_contact.name)
          # Update progress
          frappe.publish_realtime("vcf_upload_progress", {"progress": i / total_contacts, "name": full_name}, user=frappe.session.user)
      except Exception as e:
        frappe.log_error(e, _("Exception on vcf proccessing"))
        frappe.log_error(message=f'vCard: {vcard.serialize()}', title="Debug: vCard contents")
        frappe.log_error(message=f'New Contact: {new_contact.as_dict()}', title="Debug: New Contact contents")
        pass
          
    frappe.db.commit()

    return contact_names

  except vobject.base.ParseError as e:
    # Log the error and re-raise the exception
    frappe.log_error(e, _("Failed to parse VCF file. Make sure it is a well-formed vCard file."))
    raise e
  except Exception as e:
    # Log any other errors and re-raise the exception
    frappe.log_error(e, _("Failed to import VCF file due to an unexpected error"))
    raise e

def update_contact_from_vcard(contact, vcard):
  """
    Update Frappe Contact based on provided vCard.
    
    Args:
    - contact (dict): Existing Frappe Contact to be updated.
    - vcard (vobject): vCard object containing contact details.
  """

  # Extracting attributes from vCard
  first_name = vcard.n.value.given if hasattr(vcard.n.value, "given") else ""
  last_name = vcard.n.value.family if hasattr(vcard.n.value, "family") else ""
  note_value = vcard.note.value if hasattr(vcard, "note") else None
  url_value = vcard.url.value if hasattr(vcard, "url") else None

  # Fetch the existing Frappe Contact
  contact_doc = frappe.get_doc("Contact", contact.name)

  # Update the Frappe Contact's attributes
  contact_doc.first_name = first_name
  contact_doc.last_name = last_name
    
  # Set custom fields for URL and NOTE if they exist
  if url_value and hasattr(contact_doc, 'ai_web_site'):
    contact_doc.ai_web_site = url_value
  elif url_value and hasattr(contact_doc, 'cr_web_site'):  # Only if ai_web_site wasn't set
    contact_doc.cr_web_site = url_value
    
  if note_value and hasattr(contact_doc, 'ai_notes'):
    contact_doc.ai_notes = note_value
  elif note_value and hasattr(contact_doc, 'cr_notes'):  # Only if ai_notes wasn't set
    contact_doc.cr_notes = note_value

  email_value = vcard.email.value if hasattr(vcard, "email") else None

  # Here, you might want logic to update email or add if not present
  # Simplifying for this example:
  if email_value:
    contact_doc.set("email_ids", [{
      'doctype': 'Contact Email',
      'email_id': email_value,
      'is_primary': 1
    }])

  # Handling for phone numbers, similar logic might be applied to update existing numbers or add new ones
  if hasattr(vcard, "tel"):
    for tel in vcard.tel_list:
      phone_number = tel.value or ""
      contact_doc.append('phone_nos', {
        'doctype': 'Contact Phone',
        'phone': phone_number
      })
  else:
    for key in vcard.contents:
      if key.startswith('item') and key.endswith('.TEL'):
        phone_number = vcard.contents[key][0].value or ""
        contact_doc.append('phone_nos', {
          'doctype': 'Contact Phone',
          'phone': phone_number
        })

  # Generate the full_name
  full_name = vcard.fn.value or f"{first_name} {last_name}".strip()
  contact_doc.full_name = full_name
  vcard_text_content = vcard.serialize()
  contact_doc.cr_vcard_text = vcard_text_content

  # Save the updates
  contact_doc.save()

  # Return updated contact (optional)
  return contact_doc

def preprocess_vcard(vcard_string):
  # Split vCard string into lines
  lines = vcard_string.split("\n")
  # Remove the unwanted line
  lines = [line for line in lines if "_$!<HomePage>!$_" not in line]
  # Join the lines back to a string
  vcard_string = "\n".join(lines)

  return vcard_string

def synchronize_carddav_contacts():
  """Synchronize contacts from CardDAV server to Frappe."""
  # Fetch all vCards from CardDAV server
  all_vcards = fetch_vcards_from_carddav(url, username, password)
  
  for i, vcard_string in enumerate(all_vcards, 1):
    # Preprocess vCard string
    vcard_string = preprocess_vcard(vcard_string)
    vcard = vobject.readOne(vcard_string)
    #print(vcard.serialize())
    uid = vcard.uid.value if hasattr(vcard, 'uid') else None
    if not uid:
      continue  # If no UID, skip to the next vCard
    
    # Check if contact exists in Frappe
    contact_exists = frappe.db.exists("Contact", {"cr_vcard_text": ["LIKE", "%UID:" + uid + "%"]})
        
    if not contact_exists:
      #print("Creating")
      create_contacts_from_vcf(vcard_string)
      continue

    # If contact exists, fetch it
    contact = frappe.get_doc("Contact", contact_exists)
    
    # Compare the modification time
    if '-' in vcard.rev.value:
      carddav_mod_time = datetime.strptime(vcard.rev.value, "%Y-%m-%dT%H:%M:%SZ")
    else:
      carddav_mod_time = datetime.strptime(vcard.rev.value, "%Y%m%dT%H%M%SZ")
    
    frappe_mod_time = contact.modified
    # If CardDAV contact is newer, update the Frappe contact
    gap = 360 # sec is a gap between time in CardDAV Server and Frappe Server
    if carddav_mod_time.timestamp() + gap > frappe_mod_time.timestamp(): 
      #print("Updating")
      update_contact_from_vcard(contact, vcard)

def fetch_vcards_from_carddav(url, username, password):
  headers={
    'Depth': '1',
    'Content-Type': 'text/xml; charset=UTF-8',
    'User-Agent': 'Python CardDAV Client'
  }
  xml_body = """
    <d:propfind xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">
      <d:prop>
        <card:address-data />
      </d:prop>
    </d:propfind>
  """
  response = requests.request(
    'PROPFIND',
    url,
    headers=headers,
    data=xml_body,
    auth=HTTPBasicAuth(username, password)
  )
  if response.status_code != 207:
    raise Exception(f"Failed to fetch contacts. Response code: {response.status_code}")

  # Decode HTML entities from the response text
  decoded_response = html.unescape(response.text)
    
  # Extract vCards from the decoded response
  vcards = re.findall(r'BEGIN:VCARD.*?END:VCARD', decoded_response, re.DOTALL)
  return vcards

@frappe.whitelist()
def schedule_synchronization():
  enqueue(
    synchronize_carddav_contacts,
    queue='short',
    timeout=300,
    is_async=True,
    job_name="Synchronize CardDAV contacts"
  )
