## pibiCARD

cardDAV Frappe App

#### License

MIT

### Description

The pibiCard custom app is designed to extend the functionality of the Frappe framework and ERPNext by integrating it with a CardDAV server, such as NextCloud, and enhancing core DocTypes like Contact if you provide the hooks, js and py files. This app enables you to synchronize contacts between your Frappe instance and a CardDAV server.

### Configuration

To configure the pibiCard custom app, you need to include the following keys in your site_config.json file:

    carddav: The URL of the CardDAV server in the form of "https://domain.com/remote.php/dav/addressbooks/users/{username}/contacts/"
    carduser: The username for the CardDAV server
    cardkey: The API key or password for the CardDAV server

Here's an example of how your site_config.json should look like:

{
  "db_name": "your_database_name",
  "db_password": "your_database_password",
  
  ...

  "carddav": "https://domain.com/remote.php/dav/addressbooks/users/username/contacts/",
  "carduser": "your_carddav_username",
  "cardkey": "your_carddav_api_key_or_password"
}

Replace the placeholders with your actual values.

### Features
#### CardDAV Integration

Once the custom app is installed and configured, it will automatically synchronize contacts between your Frappe instance and the specified CardDAV server. You can create, update, and delete contacts in your Frappe instance, and the changes will be reflected in the CardDAV server, and vice versa. For that you need to use the vCard button on Contact Doctype Form.

#### Conclusion

The pibiCard custom app enhances the Frappe framework and ERPNext by providing seamless integration with a CardDAV server. 