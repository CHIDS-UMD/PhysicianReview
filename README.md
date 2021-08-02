# Run Google Search


```
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


```
git clone https://github.com/CHIDS-UMD/PhysicianReview.git
cd PhysicianReview/google_search/
python doctor_google_search.py --input_path=Data/DocListDF.p
```