# Lieferando / Uber Eats / Wolt parser
Context: A relative of mine asked to help a relative with parsing food delivery websites (Lieferando, Uber Eats, Wolt), which is a good opportunity for me to come back into Python and finally gain skills to parse anything I want depending on what is needed

Current Situation: 
- Current file only contains code that so far works with Lieferando.de website
- Therefore later I'll make as much code to be reusable as I can, so it worked with Uber Eats and Wolt too
- Since a lot of information is hidden behind client-side interactions, simple server-side stuff like Requests and Beautiful Soup 4 doesn't work at extracting all needed information, therefore Selenium was my go-to choice
- Websites like Lieferando.de don't wish to be parsed, therefore I am writing the code that sends responses to various popups and notifications preventing the access to their HTML DOM (cookie banners, location info etc)
