# Environment Setting
```shell
wget https://repo.anaconda.com/miniconda/Miniconda3-py39_4.10.3-Linux-x86_64.sh
bash Miniconda3-py39_4.10.3-Linux-x86_64.sh

# exit and reopen
conda create -n scrapy python=3.7
conda activate scrapy
pip install scrapy
pip install pandas
pip install requests
pip install cloudscraper
```

# Run Google Search


```
git clone https://github.com/CHIDS-UMD/PhysicianReview.git
cd PhysicianReview/google_search/
mkdir Output
python doctor_google_search.py --input_path=Data/DocListDF.p
```

# Run Yelp

```shell
cd PhysicianReview/doctor_reviews/
mkdir Output
python doctor_yelp.py --input=Data/MD_Doc2GoogleURL_yelp.p --start=0 --chunk=100
```

# Run RateMD

```shell
cd PhysicianReview/doctor_reviews/
mkdir Output
python doctor_ratemds.py --input=Data/ratemds/ratemds_v1.p --start=0 --length=10000 --chunk=100 --provider=anticaptcha --apikey=eb8b92d2448f51d53ecb93ed391b32be
```


# Run ZocDoc

```shell
# step 1: install docker in ubuntu
# https://www.cloudbooklet.com/how-to-install-docker-on-ubuntu-20-04/
sudo apt update
sudo apt upgrade
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
sudo apt update
sudo apt-cache policy docker-ce
sudo apt install docker-ce
sudo systemctl status docker
sudo docker info
```


```shell
# step2: pull scrapinghub/splash
sudo docker pull scrapinghub/splash
screen sudo docker run -it -p 8050:8050 --rm scrapinghub/splash
```

```shell
# https://praneeth-kandula.medium.com/running-chromedriver-and-selenium-in-python-on-an-aws-ec2-instance-2fb4ad633bb5

# install chrome-webdriver
cd /tmp/
wget https://chromedriver.storage.googleapis.com/2.37/chromedriver_linux64.zip
sudo apt install unzip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/bin/chromedriver
chromedriver --version
# back to home directory
cd
```


```shell
# install chrome

sudo apt-get install libxss1 libappindicator1 libindicator7
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome*.deb


curl https://intoli.com/install-google-chrome.sh | bash
sudo mv /usr/bin/google-chrome-stable /usr/bin/google-chrome
google-chrome --version && which google-chrome

```


```
python doctor_zocdoc.py --input=Data/MD_Doc2GoogleURL_zocdoc.p --start=10000 --chunk=100 --use_webdriver = False

```

# IS-Online-Review-Papers
