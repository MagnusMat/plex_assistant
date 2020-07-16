# ❱ Plex assistent

[Installation](#installation) ｜ [Konfigurering](#konfigurering) ｜ [IFTTT/DialogFlow Opsætning](#iftttdialogflow-opsætning) ｜ [Kommandoer](#kommandoer) ｜ [Hjælp med oversættelse](#oversættelse)<br><hr>

Plex assistenten er en Home Assistant komponent der tillader Google Assistant at caste Plex medier til Google cast og Plex enheder med en smule hjælp fra [IFTTT eller DialogFlow](#iftttdialogflow-setup).

For eksempel: `"Hej Google, bed Plex om at afspille The Walking Dead på Stue TV."`

Du kan benytte komponentents tjeneste uden IFTTT/DialogFlow til at kalde på kommandoer ligesom du vil. Besøg service fanen i HA's Developer Tools for at teste det.

## Støttende udvikling

- :coffee:&nbsp;&nbsp;[Køb mig en kaffe](https://www.buymeacoffee.com/FgwNR2l)
- :1st_place_medal:&nbsp;&nbsp;[Tip noget krypto](https://github.com/sponsors/maykar)
- :heart:&nbsp;&nbsp;[Støt mig på GitHub](https://github.com/sponsors/maykar)
- :keyboard:&nbsp;&nbsp;Hjælp med oversættelse, udvikling, eller dokumentation
  <br><br>

## Forfatters noter

Dette er et sideprojekt der er skabt til at udfylde manglen på indbygget Google Assistent understøttelse af Plex og fordi at Phlex/FelxTV projekterne ikke bliver udvikled på lige pt.

Dette projekt er ikke en prioritet, da Plex kunne tilføje understøttelse af Google Assistenten eller FlexTV kunne blive en mulighed igen. Når at det er sagt, så vil jeg tilføje funktioner og fikse problemer indtil at dette skulle finde sted. Jeg byder velkommen og vil stærkt værtsætte pull requests, som altid.

Tak for deres forståelse.

## Installation

Installer med en af nederstående metoder:

* **Installer med [HACS](https://hacs.xyz/):** Søg integrationer for "Plex Assistant", vælg den og tryk installer. Tilføj konfigurationen (se nedenunder) til din configuration.yaml fil.

* **Installer manuelt:** Installer denne komponent ved at kopiere alle [disse filer](https://github.com/maykar/plex_assistant/tree/master/custom_components/plex_assistant) til `/custom_components/plex_assistant/`. Tilføj konfigurationen (se nedenunder) til din configuration.yaml fil.

## Konfiguration

Add config to your configuration.yaml file.

| Nøgle        | Standard | Nødvendighed | Beskrivelse                                                                                                                                   |
|--------------|----------|--------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| url          |          | **Krævet**   | The full url to your Plex instance including port.                                                                                            |
| token        |          | **Krævet**   | Din Plex token. [Hvordan du finder din Plex token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/). |
| default_cast |          | Valgfri      | Navnet på casting enheden anvender vhis der ikke er et givet.                                                                                 |
| language     | 'dk'     | Valgfri      | Language code. See Below for supported Languages.                                                                                             |
| tts_errors   | true     | Valgfri      | Will speak errors on the selected cast device. For example: when the specified media wasn't found.                                            |
| aliases      |          | Valgfri      | Set alias names for your devices. Example below, set what you want to call it then it's actual name or machine ID.                            |
| cast_delay   | 6        | Valgfri      | This delay helps prevent "Sorry, something went wrong" and grey screen errors. [Se nedenunder for mere info.](#cast-forsinkelse)              |

<hr>

**Eksempel konfiguration**

```Python
plex_assistant:
  url: 'http://192.168.1.3:32400'
  token: 'tH1s1Sy0uRT0k3n'
  default_cast: 'Stue TV'
  language: 'dk'
  tts_errors: true
  aliases:
    Downstairs TV: TV0565124
    Upstairs TV: Samsung_66585
```

## Kompangon sensor

Plex Assistenten inkluderer en sensor til at vise navnene på forbundede enheder og Plex klienternes machine ID. Dette er for at hjælpe med konfigurering og fejlfinding. For at opdatere sensoren, send kommandoen "update sensor" til Plex Assistenten, enter gennem Google Assistenten eller som et HA service kald.

```Python
sensor:
- platform: plex_assistant
```

***Du skal genstarte efter installation og konfigurering, du kan opstille IFTTT eller DialogFlow med instruktionerne nedenunder, før at du genstarter.***

## IFTTT/DialogFlow opstilling

You can either use IFTTT or DialogFlow to trigger Plex Assistant. IFTTT is the easiest way to set this up, DialogFlow is more involved and has some quirks. The advantage to using Dialogflow is it's support for more languages (as long as the translation has been made for Plex Assistant, see below).

#### Understøttede sprog
Plex Assistenten understøtter: Engelsk (en), svensk (sv), hollandsk (nl), frensk (fr), og italiensk (it) med DialogFlow. [Hjælp med oversættelser.](#translation)

<details>
  <summary><b>IFTTT opstillings guide</b></summary>

## IFTTT opstilling

#### Med Home Assistenten

* Go to "Configuration" in your HA sidebar and select "Integrations"
* Hit the add button and search for "IFTTT" and click configure.
* Follow the on screen instructions.
* Copy or save the URL that is displayed at the end, we'll need it later and it won't be shown again.
* Click "Finish"

#### Med IFTTT

Visit [ifttt.com](https://ifttt.com/) and sign up or sign in.

* Click "Explore" in the top right, then hit the plus sign to make your own applet from scratch
* Press the plus sign next to "If". Search for and select "Google Assistant"
* Select "Say phrase with text ingredient"

Now you can select how you want to trigger this service, you can select up to 3 ways to invoke it. I use things like `tell plex to $` or `have plex $`. The dollar sign will be the phrase sent to this component. See currently supported [commands below](#commands)). You can also set a response from the Google Assistant if you'd like. Hit "Create Trigger" to continue.

* Press the plus sign next to "Then"
* Search for and select "Webhooks", then select "Make a web request"
* In the URL field enter the webhook URL HA provided you earlier
* Select method "Post" and content type "application/json"
* Then copy and paste the code below into the body field

`{ "action": "call_service", "service": "plex_assistant.command", "command": "{{TextField}}" }`

#### Med Home Assistant

Finally, add the following automation to your Home Assistant configuration.yaml:

```Python
automation:
  - alias: Plex Assistant Automation
    trigger:
    - event_data:
        action: call_service
      event_type: ifttt_webhook_received
      platform: event
    condition:
      condition: template
      value_template: "{{ trigger.event.data.service == 'plex_assistant.command' }}"
    action:
    - data_template:
        command: "{{ trigger.event.data.command }}"
      service_template: '{{ trigger.event.data.service }}'
```

***Either refresh your automations or restart after adding the automation.***

</details>

<details>

  <summary><b>DialogFlow opstillings guide</b></summary>

## DialogFlow opstilling

#### Med Home Assistant

* Go to "Configuration" in your HA sidebar and select "Integrations"
* Hit the add button and search for "Dialogflow".
* Copy or save the URL that is displayed, we'll need it later and it won't be shown again.
* Click "Finish"

#### Med DialogFlow

Besøg <https://dialogflow.com/> og tilmeld dig eller log ind.
Keep going until you get to the "Welcome to Dialogflow!" page with "Create Agent" in the sidebar.

- Click on Create Agent and Type "Plex_Assistant" as the agent name and select "Create"
- Now select "Fulfillment" in the sidebar and enable "Webhook"
- Enter the "URL" Home Assistant provided us earlier, scroll down and click "Save"
- Now select "Intents" in the sidebar and hit the "Create Intent" button.
- Select "ADD PARAMETERS AND ACTION" and enter "Plex" as the action name.
- Check the checkbox under "Required"
- Under "Parameter Name" put "command", under "Entity" put "@sys.any", and under "Value" put "$command"
- Now click "ADD TRAINING PHRASES"
- Create a phrase and type in "command"
- Then double click on the word "command" you just entered and select "@sys.any:command"
- Scroll to the bottom and expand "Fulfillment" then click "ENABLE FULFILLMENT"
- Turn on "Enable webhook call for this intent"
- Expand "Responses" turn on “Set this intent as end of conversation”
- At the top of the page enter "Plex" for the intent name and hit "Save"
- On the right side of the page hit "Set-up Google Assistant integration"
- Click the space under "Explicit invocation", select "Plex", then hit "Close"
- Type "Plex" in "Implicit invocation", then click "Manage assistant app"
- Click "Decide how your action is invoked"
- Under "Display Name" type "Plex" then hit save in the top right (it may give an error, but thats okay).

#### Med Home Assistant

Tilføj det nederstående til din `configuration.yaml` fil

```Python
intent_script:
  Plex:
    speech:
      text: Command sent to Plex.
    action:
      - service_template: plex_assistant.command
        data_template:
          command: "{{command}}"
```

You can now trigger Plex Assistant by saying "Hey Google, tell plex to..." or "Hey Google, ask plex to..."

***Genstart efter du har tilføjer der overstående.***

</details>

## Kommandoer

#### Fuzzy Matching

A show or movie's title and the Chromecast device used in your phrase are processed using a fuzzy search. Meaning it will select the closest match using your Plex media titles and available cast device names. `"play walk in deed on the dawn tee"` would become `"Play The Walking Dead on the Downstairs TV."`. This even works for partial matches. `play Pets 2` will match `The Secret Life of Pets 2`.

#### Du kan sige ting som:

- `"play the latest episode of Breaking Bad on the Living Room TV"`
- `"play unwatched breaking bad"`
- `"play Breaking Bad"`
- `"play Pets 2 on the Kitchen Chromecast"`
- `"play ondeck"`
- `"play ondeck movies"`
- `"play season 1 episode 3 of The Simpsons"`
- `"play first season second episode of Taskmaster on the Theater System"`

### Kontrol kommandoer:

- `play`
- `pause`
- `stop`
- `jump forward`
- `jump back`

Be sure to add the name of the device to control commands if it is not the default device. `"stop downstairs tv"`.

I've tried to take into account many different ways that commands could be phrased. If you find a phrase that isn't working and you feel should be implemented, please make an issue.

***Music isn't built in yet, only shows and movies at the moment.***

#### Cast enhed

If no cast device is specified the default_cast device set in config is used. A cast device will only be found if at the end of the command and when preceded with the word `"on"` or words `"on the"`. Example: *"play friends **ON** downstairs tv"*

## Cast forsinkelse

A delay (in seconds) is used to help prevent grey screen and "Sorry, something went wrong" errors that can happen on some cast devices. This setting has no effect on Plex Clients, only Google Cast devices.

If you are having these issues you can test the delay needed by using the `plex_assistant.command` service found in `Developer Tools > Services`. The example below will test the needed delay on the device named "Downstairs TV":

```Python
command: Play Evil Dead on the Downstairs TV
cast_delay: 7
```

The amount of delay needed is typically the time it takes from when the screen turns black after calling the service to when you see the show info on screen. Test this with nothing playing on the device and with something already playing on the device as well.

The default delay per device is 6 seconds. By using this config option you can set the delay per device, see example below:

```Python
plex_assistant:
  url: 'http://192.168.1.3:32400'
  token: 'tH1s1Sy0uRT0k3n'
  default_cast: 'Downstairs TV'
  cast_delay:
    Downstairs TV: 7
```

## Oversættelse

Du kan bidrage til oversættelsen/lokaliseringen af denne komponent ved at bruge [øversættelses guiden](translation.md).
