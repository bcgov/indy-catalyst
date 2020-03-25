
# Running the Aries VCR Credential Registry

TODO overview


## How can I run the Credential Registry?

You need to have a local Indy network running, you can use VON Network which is available here:  https://github.com/bcgov/von-network

```
git clone https://github.com/bcgov/von-network.git
cd von-network
./manage build
./manage start
```

Once this is running, simply clone, build and run Aries VCR as follows:

```
https://github.com/hyperledger/aries-vcr
cd aries-vcr/starter-kits/docker
THEME_PATH=/path/to/aries-vcr/client/themes/ THEME=bcgov ./manage build
THEME=bcgov ./manage start seed=my_seed_000000000000000000000123
```

Note this runs with the bcgov theme.  TO run with the default theme replace the last two commands with:

```
./manage build
./manage start seed=my_seed_000000000000000000000123
```


## Is there a demo Issuer available?

There is a demo Issuer available here:  https://github.com/bcgov/indy-catalyst-issuer-controller

There is also a more robust Issuer available here:  https://github.com/bcgov/von-bc-registries-agent


## How can I run the credential registry from my own fork?

You will need your own fork if you intend to:

- Customize the Aries VCR code
- Update the code (fix bugs, add features) that you intend to submit back to bcgov

Simply fork the https://github.com/hyperledger/aries-vcr repository on github to create your own fork.

When you create a local clone, add the bcgov repo as an "upstream" as follows:

```
https://github.com/<you>/aries-vcr
cd aries-vcr
git remote add upstream https://github.com/hyperledger/aries-vcr
git remote -v
```

Depending on how much you customize the Aries VCR code, you can keep your own fork up-do-date as follows:

```
git fetch upstream
git merge upstream/master
```

If you made any changes to core code, you may have to manually resolve conflicts.


## How can I customize the Credential Registry?

### Customizing the User Interface

The default theme and code is under the "default" theme.

If you add a custom theme it will look there first.

It follows standard Angular practices ...


### Customizing the Back-end Python Code

There is a "custom theme" file for the back-end Python code, examples are:

- app/app/custom_settings_bcgov.py
- app/app/custom_settings_ongov.py

Just name your file "app/app/custom_settings_<theme>.py"

Build the Credential Registry as follows (use your theme name):

```
THEME_PATH=/path/to/aries-vcr/client/themes/ THEME=bcgov ./manage build
THEME=bcgov ./manage start seed=my_seed_000000000000000000000123
```

Custom settings are loaded from "app/settings.py" (search for "custom_settings_file").

There is some code in "api_v2/utils.py" that you can use to get custom settings (from your own code).


### Adding a new Web Service

Updates to the back-end to add a new web service:

1. Add/update any models as required, and then generate migrations
2. Add/update serializers (based on the output format of the new services)
3. Add a view to support the service
4. Add a URL
5. See documentation around the "custom Python behaviour" code
6. Not sure if the openapi.yml file is acually used ...

Updates to the front end to consume the service:

1. Add a mapping for the service output data to data-types.ts
2. Shouldn't need to update general-data.service.ts
3. Update html and typescript as necessary to consume the new service and display the results

Note that there can be html in the default theme as well as your custom theme - you should only reference your custom web service in your custom theme's html.

Check the following commit for an example of changes requried to add a new web service:

https://github.com/bcgov/TheOrgBook/commit/89e6178e5466b8be160f7376bfc6e222a28e2633

