frappe.ui.form.on('Contact', {
  onload: function (frm) {
    var template = '';

    if (frm.doc.__islocal) {
      // QR Preview
      template = '<img src="" />';
      frm.set_df_property('cr_qr_preview', 'options', frappe.render_template(template));
      frm.refresh_field('cr_qr_preview');
    } else {
       // QR Preview
       template = '<img src="' + frm.doc.cr_qr_code + '" width="300px"/>';
       frm.set_df_property('cr_qr_preview', 'options', frappe.render_template(template));
       frm.refresh_field('cr_qr_preview');
    }
  },
  refresh: function (frm) {
    let ai_web_site = document.querySelector('.frappe-control[data-fieldname="ai_web_site"]');
    let ai_notes = document.querySelector('.frappe-control[data-fieldname="ai_notes"]');
    if (ai_web_site) {
      document.querySelector('.frappe-control[data-fieldname="cr_web_site"]').style.display = 'none'
    }
    if (ai_notes) {
      document.querySelector('.frappe-control[data-fieldname="cr_notes"]').style.display = 'none'
    }
    if (!frm.doc.__islocal) {
      frm.add_custom_button(__("vCard Create"), function () {
        frappe.call({
          method: 'pibicard.overrides.contact.build_vcard',
          args: {
            contact_name: frm.doc.name
          },
          callback: function (response) {
            if (response.message) {
              frm.set_value('cr_vcard_text', response.message);
              frappe.show_alert({
                message: __('vCard generated successfully.'),
                indicator: 'green'
              });
            }
          }
        });
      }, __("vCard"));
      //
      if (frm.doc.cr_vcard_text) {
        frm.add_custom_button(__("vCard Download"), function () {
          // Create a Blob from the vCard text
          var vcardBlob = new Blob([frm.doc.cr_vcard_text], { type: "text/vcard;charset=utf-8" });
          // Create a temporary download link
          var downloadLink = document.createElement('a');
          downloadLink.href = window.URL.createObjectURL(vcardBlob);
          downloadLink.download = frm.doc.first_name + '_' + frm.doc.last_name + '.vcf';
          // Append the link to the document, click it, and remove it
          document.body.appendChild(downloadLink);
          downloadLink.click();
          document.body.removeChild(downloadLink);
        }, __("vCard"));

        frm.add_custom_button(__("vCard QR Code"), function () {
          var logo = null;
          if (frm.doc.cr_logo) {
            logo = frm.doc.cr_logo;
          } else {
            logo = null;
          }
          if (frm.doc.cr_vcard_text) {
            frappe.call({
              method: 'pibicard.overrides.contact.get_qrcode',
              args: {
                input_data: frm.doc.cr_vcard_text,
                logo: logo
              },
              callback: function (response) {
                if (response.message) {
                  frm.set_value('cr_qr_code', response.message);
                  frappe.show_alert({
                    message: __('QR Code generated successfully.'),
                    indicator: 'green'
                  });
                  var template = '<img src="' + response.message + '" width="300px"/>';
                  frm.set_df_property('cr_qr_preview', 'options', frappe.render_template(template));
                  frm.refresh_field('cr_qr_preview');

                  frm.save();
                }
              }
            });
          } else {
            frappe.throw({
              message: __('First generate the vCard'),
              indicator: 'red'
            });
          }
        }, __("vCard"));
        //        
        if (frm.doc.cr_vcard_text) {
          frm.add_custom_button(__("vCard Integration"), function () {
                 
            frappe.call({
              method: 'pibicard.overrides.contact.get_site_config_values',
              args: {
                keys: 'carddav,carduser,cardkey',  // Replace with the keys you want to access
              },
              callback: function(response) {
                if (response.message) {
                  var value = response.message;
                  const url = value['carddav'];
                  const username = value['carduser'];
                  const password = value['cardkey'];
                  const vcard_text = frm.doc.cr_vcard_text;
                    
                  frappe.call({
                    method: 'pibicard.overrides.contact.upload_vcard_to_carddav',
                    args: {
                      url: url,
                      username: username,
                      password: password,
                      vcard_string: vcard_text
                    },
                    callback: function(res) {
                      if (res.message){
                        console.log(res.message);
                      }
                    }
                  });

                }
              }
            });
                                      
          }, __("vCard"));
        }
      }
    }
  }
});