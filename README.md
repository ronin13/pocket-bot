Pocket Bot
===========

![Pocket Bot](images/bot-icon3.png)
![getpocket logo](images/pocket-logo2.png)

[Pocket](https://getpocket.com) facebook messenger bot built using [awslabs/chalice](https://github.com/awslabs/chalice), and runs on AWS Lambda and AWS API Gateway.
[Getpocket API](https://getpocket.com/developer/) is used to add URLs.

AWS S3 is used for persistence across runs, since this is serverless, state has to be maintained somewhere.

OAuth2 authentication is handled by the bot.

More details and screenshots coming soon!

-   Free software: MIT license

Why 
--------
When using facebook on mobile, it is not possible to share articles
to services such as getpocket.com. Due to the nature of facebook api, facebook saves cannot be synced externally either.
However, one can still share link to a person or a bot in this case. 
This bot authenticates the user if not authenticated already, and saves any URLs the user sends/shares to their pocket account.


Credits
-------

This package was created with
[Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage)
project template.

[Bot logo](https://pixabay.com/p-807306/?no_redirect)

Not affiliated with getpocket.com.
