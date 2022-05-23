

# Data Collection

## Data Collection Procedure

![Data Collection Procedure](_etc/workflow.png)

The above figure shows the data collection procedure.

## Physician Directory
We used the Centers for Medicare & Medicaid Services National Plan and Provider Enumeration System (NPPES) to identify all physicians in the United States. Only individual National Provider Identifiers (Entity Type Code=1) whose business practice addresses are located inside the United States were included. We focus on all healthcare professionals in the NPPES system with a credential of either MD (Doctor of Medicine) or DO (Doctor of Osteopathic Medicine), which resulted in 1,141,176 physicians. See the Folder [doctor_directory](doctor_directory) for the code and data source.


## Google Search

Google Search: To best capture the online reviews that a patient can retrieve, we followed what we expect is a typical strategy for patients looking for physicians. We searched for each physician on Google Search1 using a query that combined each physician’s full name, city and state of practice, and specialty.  See the Folder [doctor_directory](doctor_directory) for the code and data source. We generated NPI to Search Keywords in this folder.


For each query, the search results (URLs) that showed up in the first two pages (usually 20 URLs) were then saved. In total, 19,944,916 URLs were extracted from all the search results, which covered 1,058,331 (92.74%) physicians and pointed to various websites. 

See the Folder [google_search](google_search) for more information. The URL2SearchKeyword is in the folder [google_search/Data](google_search/Data). The summary of collected URL files is reported in file [URLReport.csv](google_search/Output/URLReport.csv)


## Physician Online Review Websites
Based on all websites returned in the search results, we identified the top online physician review platforms: Healthgrades (737,126), Vitals (774,083), RateMDs (178,888), ZocDoc (179,180), and Yelp (39,344). We then focused on these five platforms for our examination of online review information. See the summary of collected URL files [URLReport.csv](google_search/Output/URLReport.csv) for more information.

## Physician Profile Collection
We developed Python scripts to download the online reviews. Our Python scripts went through all URLs identified for the five online review platforms. The collection is time-consuming, the related code and data information is in the [doctor_reviews](doctor_reviews) folder.


### Physician Cleansing
After collecting all the data, we first filter for only the valid physicians. 
There were sometimes multiple, slightly different URLs pointing to different pages/sections of the same physician’s profile page. 

To construct the clean sample, we removed duplicated profile pages from the search results. The information collected includes each physician’s basic profile data, which we used to verify that the profile corresponds to the correct physician and online reviews. We also identified the duplicated and unmatched physicians from the dataset. 

After dropping mismatched and duplicated profiles and physicians with invalid profile scores, the number of physicians identified on each platform is: 719,717 (2,148,323 reviews) for Healthgrades, 720,293 (6,063,074 reviews) for Vitals, 152,678 (296,904 reviews) for RateMDs, 167,996 (901,681 reviews) for ZocDoc, and 30,902 (221,984 reviews) for Yelp. 

<!-- This detailed information for physician cleansing is in the file [PhysicianReport](final_analysis/PhysicianReport.csv). -->

### Why do we exclude ZocDoc?
Of the five platforms, 56.80% of ZocDoc reviews are not clearly labeled with an exact posting time. Therefore, we focused on the other four platforms and excluded ZocDoc from our main analyses. As a robustness test, we also included the 43.20% of the ZocDoc reviews that provided a timestamp and found consistent results.




# Environment Setting 

To reproduce the data collection procedure, you need first set up the environment. 

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

git clone https://github.com/CHIDS-UMD/PhysicianReview.git

```

Once the environment is set up, you can run all the codes in this repository.


