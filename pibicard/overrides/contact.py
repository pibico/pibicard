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

from datetime import datetime

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
    
  # Fetch CardDAV details
  url = frappe.conf.get('carddav')
  username = frappe.conf.get('carduser')
  password = frappe.conf.get('cardkey')

  for i, contact_name in enumerate(contact_names, 1):
    contact = frappe.get_doc("Contact", contact_name)
    
    # If vcard_string is empty, generate it with build_vcard method
    if not contact.cr_vcard_text:
      contact.cr_vcard_text = build_vcard(contact_name)
      
    upload_vcard_to_carddav(
      url,
      username,
      password,
      contact.cr_vcard_text
    )
    # Calculate progress percentage and publish realtime
    progress = (i / total_contacts) * 100
    frappe.publish_realtime('upload_vcards_progress', {'progress': progress}, user=frappe.session.user)

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
def upload_vcard_to_carddav(url, username, password, vcard_string):
  # Parse the vCard string into a vobject
  vcard = vobject.readOne(vcard_string)
  # Get the vCard UID
  uid = vcard.uid.value
  vcard_url = f"{url}/{uid}.vcf"
  # Check if vCard exists
  response = requests.get(vcard_url, auth=HTTPBasicAuth(username, password))
  if response.status_code == 200:
    # If vCard exists, update it
    response = requests.put(vcard_url, data=vcard_string, headers={"Content-Type": "text/vcard"}, auth=HTTPBasicAuth(username, password))
  elif response.status_code == 404:
    # If vCard does not exist, create a new one
    response = requests.put(vcard_url, data=vcard_string, headers={"Content-Type": "text/vcard"}, auth=HTTPBasicAuth(username, password))
  else:
    frappe.throw(f"Error checking vCard existence for {uid}: {response.status_code}")

  if response.status_code not in [201, 204]:
    frappe.throw(f"Error uploading/updating vCard for {uid}: {response.status_code}")
  else:
   frappe.msgprint(f"vCard for {uid} uploaded/updated successfully")
   
@frappe.whitelist()
def create_contacts_from_vcf(vcf_content):
    try:
        # Parse the VCF content using vobject
        contact_names = []
        total_contacts = sum(1 for _ in vobject.readComponents(vcf_content))  # Calculate total contacts

        for i, vcard in enumerate(vobject.readComponents(vcf_content)):
            # Extract the first_name and last_name from the vCard
            first_name = vcard.n.value.given if hasattr(vcard.n.value, "given") else ""
            last_name = vcard.n.value.family if hasattr(vcard.n.value, "family") else ""

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
                'web_site': vcard.url.value if hasattr(vcard, "url") else "",
            })

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
            full_name = f"{first_name} {last_name}".strip()
            new_contact.full_name = full_name

            existing_contact = frappe.db.exists("Contact", {"full_name": full_name}) if full_name else None
            if existing_contact:
                continue
            else:
                # Save the new contact
                new_contact.flags.from_vcf = True

                # Debugging information
                frappe.log_error(message=f'vCard: {vcard.serialize()}', title="Debug: vCard contents")
                frappe.log_error(message=f'New Contact: {new_contact.as_dict()}', title="Debug: New Contact contents")

                new_contact.insert(ignore_permissions=True)
                contact_names.append(new_contact.name)
                # Update progress
                frappe.publish_realtime("vcf_upload_progress", {"progress": i / total_contacts}, user=frappe.session.user)

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