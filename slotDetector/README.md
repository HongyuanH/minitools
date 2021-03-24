# slotDetector
ASDA delivery slot detector used during the outbreak of Covid-19 pandemic. It hasn't been used for quite some time so does not function properly.

This tool uses `smtplib` to auto login to Gmail for sending notifications. **Less secure app access** must be enabled [here](https://www.google.com/settings/security/lesssecureapps) for the account.

Install dependencies:

```python
pip install -r requirements.txt
```

Update `cfg.yaml` as shown in the below example:

```yaml
---
# set to true for the first time and do a normal sign-in using the Chrome pop-up window
# set to false afterwords so that Chrome can auto login and find slots
first_time: true 

# email address for sending notifications
email: 'superman@gmail.com' 

# password for the above email
passwd: 'superpassword' 

# email list for receiving notifications
send_to: 
  - 'batman@gmail.com' 
  - 'spiderman@gmail.com'
```

Run:

```python
python slotDetector.py
```

Do a normal sign-in using the Chrome pop-up window and exit. Then open `cfg.yaml`, change `first_time` to `false`, and run again:

```python
python slotDetector.py
```

It will search for available slots every 60 seconds and send email notifications if found any.