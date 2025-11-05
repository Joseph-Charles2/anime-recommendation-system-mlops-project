from setuptools import setup, find_packages
import pathlib

HERE = pathlib.Path(__file__).parent
LONG_DESCRIPTION = (HERE/"README.md").read_text(encoding='utf-8')

HYPEN_E_DOT = "-e ."
def get_requirements(file_path):
    with open (file_path,'r') as f:
        requirements = f.readlines()
        requirements = [line.strip() for line in requirements]
        requirements = [lines for lines in requirements if lines !=HYPEN_E_DOT]
    return requirements


setup(
    name ='ml-project-2',
    version = '0.0.1',
    description = 'A Anime Recommendation System ',
    long_description_content_type ='text/markdown',
    url = 'https://github.com/Joseph-Charles2/anime-recommendation-system-mlops-project',
    author = 'Joseph Charles',
    author_email = 'josephcharles.19988@gmail.com',
    packages = find_packages(),
    install_requires = get_requirements("requirements.txt")

)
