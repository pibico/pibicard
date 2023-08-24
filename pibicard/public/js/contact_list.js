frappe.listview_settings['Contact'] = {
  onload: function(listview) {
  	listview.page.add_menu_item(__('Import vCard'), function() {
      // Create a file input element
      let fileInput = document.createElement('input');
      fileInput.type = 'file';
      fileInput.accept = '.vcf';
      
      fileInput.onchange = function() {
        let file = fileInput.files[0];
        // Use FileReader to read the file's content
        let reader = new FileReader();

        reader.onload = function(e) {
          let vcfContent = e.target.result;  
          // Call your server-side method
          frappe.call({
            method: 'pibicard.overrides.contact.create_contacts_from_vcf',
            args: {
              vcf_content: vcfContent
            },
            callback: function(response) {
              try {
                if (response.exc) {
                  // Error handling if the server method fails
                  frappe.msgprint(__('Failed to import VCF file. Please make sure it is a well-formed vCard file.'));
                } else {
                  // Refresh the list view
                  listview.refresh();
                }
              } finally {  
                isUploading = false; // Clear the flag
              }
            }
          });
        };
        reader.readAsText(file);
      };
      // Trigger the file input dialog
      fileInput.click();
    });
    
    // Add a menu item for generating contact book
    listview.page.add_menu_item(__('Generate vCard Book'), function() {
      var selected_contacts = listview.get_checked_items();
            
      if (selected_contacts.length === 0) {
        frappe.msgprint(__('No contacts selected.'));
        return;
      }
            
      // Create an array to store the vCards
      var vcards = [];
            
      // Iterate over selected contacts
      selected_contacts.forEach(function(contact) {
        // Call the server-side method to build vCard for each contact
        frappe.call({
          method: 'pibicard.overrides.contact.build_vcard',
          args: {
            contact_name: contact.name
          },
          callback: function(response) {
            if (response.message) {
              // Append the vCard to the array
              vcards.push(response.message);
                            
              // Check if all vCards have been generated
              if (vcards.length === selected_contacts.length) {
                // Combine vCards into a single contact book file
                var contact_book = vcards.join('\n\n');
                                
                // Trigger the file download
                var blob = new Blob([contact_book], { type: 'text/vcard' });
                var url = URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = 'contact_book.vcf';
                a.click();
              }
            } else if (response.exc) {
              // Error handling if the server method fails
              frappe.msgprint(__('Failed to generate vCard for contact {0}.', [contact.name]));
            }
          }
        });
      });
    });
    
    // Add a menu item for integrating contact book
    listview.page.add_menu_item(__('Integrate Vcard Book'), function() {
      var selected_contacts = listview.get_checked_items();

      if (selected_contacts.length === 0) {
        frappe.msgprint(__('No contacts selected.'));
        return;
      }

      var contact_names = selected_contacts.map(function(contact) {
        return contact.name;
      });
      
      frappe.call({
        method: 'pibicard.overrides.contact.enqueue_upload_vcards_to_carddav',
        args: {
          'contact_names': JSON.stringify(contact_names)
        },
        callback: function(response) {
          // The job has been enqueued, you can also display a message here
          console.log('Job enqueued:', response.message);
        },
        always: function() {
          // Hide the progress bar when job is finished
          frappe.hide_progress();
        }
      });
    });

  }
}