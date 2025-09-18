# VFS France Appointment Bot

This project provides a Selenium-based automation helper that can monitor and
book available appointment slots on the VFS Global portal for France. The bot
reads a YAML configuration file that contains your login credentials, desired
appointment preferences, and the CSS/XPath selectors that match the current
layout of the VFS website.

> **Important:** Review the VFS Global terms of service before using this
> automation and make sure you are allowed to automate booking for your account.
> Keep your personal data safe and never commit sensitive information to the
> repository.

## Project layout

- `vfsbot/` – Python package containing the Selenium automation logic.
- `main.py` – command line interface that loads a configuration file and runs
  the bot.
- `config.example.yaml` – starter configuration you can copy and update with
  your own credentials, appointment preferences, and DOM selectors.
- `requirements.txt` – Python dependencies required by the automation script.

## Getting started

1. Create and activate a Python 3.11+ virtual environment.
2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `config.example.yaml` to `config.yaml` and update:

   - `credentials` with your VFS email and password.
   - `applicant` details with the passport holder’s information.
   - `appointment` preferences with the center, visa category, and desired
     slots you want to monitor.
   - `selectors` with CSS/XPath expressions that match the current HTML of the
     VFS portal. Inspect the elements in your browser’s developer tools and
     adjust the selectors if the defaults do not match.

4. Make sure the matching Chrome browser and [ChromeDriver](https://chromedriver.chromium.org/downloads)
   version is available on your system path. Alternatively, set the
   `webdriver.executable_path` value in the configuration file.

5. Run the bot:

   ```bash
   python main.py config.yaml --headless
   ```

   Omit `--headless` if you want to observe the browser activity.

## How it works

1. The bot signs in to the VFS portal using the provided credentials.
2. It opens the appointment page and selects the configured visa center and
   categories.
3. The automation polls the calendar for open dates, matching them against the
   preferred dates and times. If you do not provide preferred slots, the first
   available slot is selected.
4. Once a suitable slot is found, the script fills in the applicant’s passport
   details and completes the confirmation flow.

If no matching slot is found within the configured number of polling attempts,
`BookingError` is raised and the script exits with status code `1`.

## Customising the selectors

Every installation of the VFS portal might ship with slightly different HTML
structure. The selectors in `config.example.yaml` are intentionally verbose so
that each form field has a dedicated key. If any selector fails, the bot raises
an error indicating the missing or incompatible locator. Update the selector in
your configuration file to match the actual DOM.

For fields not covered by the default mapping, add an entry to
`applicant.additional_fields` and define the selector with the exact same key in
`selectors`.

## Safety tips

- Store your `config.yaml` outside of version control or add it to `.gitignore`.
- Use environment variables or secrets management services for real deployments.
- Monitor the automation while it is running to ensure the website has not
  changed its flow or introduced captchas.

## Disclaimer

This project is provided for educational purposes. You are responsible for
complying with VFS Global’s rules and regulations when using automation tools.
