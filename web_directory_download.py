from selenium import webdriver
from selenium.common.exceptions import *
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from getpass import getpass
import os

# Global variables
visited_files = set()  # Visited files in the catalogues
dict_files = dict()  # Stores a path of a source file and a new path to move


def init_driver(headless: bool = True, download_path: str = "C:/"):
    """
    Initialize a Selenium Chrome driver with desired visibility option.
    :return: webdriver: webdriver.Chrome
    """
    options = webdriver.ChromeOptions()
    options.add_argument(f"download.default_directory={download_path}")
    if headless:
        options.add_argument("--headless")
    service = webdriver.ChromeService()
    return webdriver.Chrome(options, service)


def parse_webpage(url: str, credentials: dict, paths: dict, headless: bool):
    """
    Sign in the website and parse all files on the webpage downloading them and ordering them in the same structure as
    on the webpage.

    :param url: link to the webpage
    :param credentials: login and password
    :param paths: path to the source location ('source') and path to download folder ('download')
    :param headless: invisibility of the browser (True/False)
    :return: None
    """

    driver = init_driver(headless, paths["download"])
    try:
        driver.get(url)

        # Signing in
        driver.find_element(By.ID, "username").send_keys(credentials["login"])
        driver.find_element(By.ID, "password").send_keys(credentials["password"])
        driver.find_element(By.ID, "loginbtn").click()

        # Recursive parsing of directories
        modules = driver.find_elements(By.CLASS_NAME, "contentwithoutlink ")
        for module in modules:
            parse_directory(paths['source'],
                            module.find_elements(By.CLASS_NAME, "ygtvitem")[1], driver)
        driver.close()
    except NoSuchElementException as e:
        print(e.msg)
        return
    except WebDriverException as e:
        print(
            f"An error has occurred with the driver! Check the validity of the path: {webpage_url} and inspect the "
            f"error message: {e.msg}")
        return

    try:
        # Moving files
        for key, value in dict_files.items():
            move_to_download_folder(paths["download"] + key, value)
    except FileNotFoundError as e:
        print(f"The path to the source file({e.args['path']})")


def parse_directory(cur_path: str, element: WebElement, driver: webdriver.Chrome):
    """
    Parse files in the directory

    :param cur_path: current directory
    :param element: webelement representing a directory
    :param driver: webdriver
    :return: None
    """
    global visited_files, dict_files
    # Parsing directory or file name
    try:
        dir_name = element.find_elements(By.CLASS_NAME, "fp-filename")[0].text
        if dir_name in visited_files:
            return
        cur_path = cur_path + "/" + dir_name
        if not os.path.exists(cur_path):
            os.mkdir(cur_path)
        # Parsing children
        children = element.find_elements(By.CLASS_NAME, "ygtvchildren")[0]
        for child in children.find_elements(By.CLASS_NAME, "ygtvitem"):
            if len(child.find_elements(By.CLASS_NAME, "ygtvitem")) == 0:
                block = child.find_elements(By.TAG_NAME, "table")[0]
                file = block.find_element(By.CLASS_NAME, "fp-filename-icon").find_element(By.TAG_NAME, "a")
                file_name = block.find_elements(By.CLASS_NAME, "fp-filename")[0].text
                driver.get(file.get_attribute("href"))
                if file_name:
                    dict_files.setdefault(file_name, cur_path + "/" + file_name)
                visited_files.add(file_name)
            else:
                parse_directory(cur_path, child, driver)
    except NoSuchElementException as e:
        print(e.msg)
        return
    except NoSuchAttributeException as e:
        print(e.msg)
        return


def move_to_download_folder(old_path: str, new_path: str) -> None:
    """
    Move the source file to the desired destination location
    and delete the initial source file. Raise FileNotFoundError upon failure.

    :param old_path: the path of the source file
    :param new_path: the path to the destination file
    :return: None
    """
    if not os.path.exists(old_path):
        raise FileNotFoundError(path=old_path)
    with open(old_path, "rb") as old_file:
        try:
            new_file = open(new_path, "wb")
            new_file.write(old_file.read())
            new_file.close()
        except FileNotFoundError:
            print(f"The path {new_path} is incorrect!")
    os.remove(old_path)


if __name__ == '__main__':
    webpage_url = input("Input the webpage url: ")
    login = input("Input the login to sign in: ")
    password = getpass("Input the password: ")
    save_path = input("Input the path where directories and files will be saved: ")
    download_path = input("Input the path where files will be temporarily downloaded: ")
    headless_param = input("Do you want to see the browser? (Yes / No): ") == "Yes"
    parse_webpage(webpage_url, {"login": login, "password": password}, {"source": save_path, "download": download_path},
                  headless_param)
