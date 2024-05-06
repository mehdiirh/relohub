from time import sleep

from django.conf import settings
from selenium import webdriver
from selenium.webdriver.common.by import By

from linkedin.models import LinkedinAccount


def update_linkedin_cookies_with_selenium():
    for account in LinkedinAccount.objects.filter(is_active=True):
        options = webdriver.FirefoxOptions()

        if settings.SELENIUM_HEADLESS:
            options.add_argument("--headless")

        profile = webdriver.FirefoxProfile()
        profile.set_preference("network.proxy.type", 0)
        options.profile = profile

        driver = webdriver.Firefox(options=options)
        driver.get(
            "https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin"
        )

        username = driver.find_element(value="username")
        password = driver.find_element(value="password")
        login = driver.find_element(
            By.CSS_SELECTOR,
            value="#organic-div > form > div.login__form_action_container > button",
        )

        sleep(1)
        username.send_keys(account.username)
        password.send_keys(account.password)
        sleep(1)
        login.click()

        driver.implicitly_wait(10)

        if "feed" not in driver.current_url:
            print()
            print(driver.current_url)
            input(
                "Manual login required. Check the browser and then press any key to continue: "
            )

        cookies = {cookie["name"]: cookie["value"] for cookie in driver.get_cookies()}
        account.cookies = cookies
        account.save()

        driver.close()
