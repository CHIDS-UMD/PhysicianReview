
# Run Google Search


If there is no `Output` folder: 
```
cd PhysicianReview/google_search/
mkdir Output

```

To search for the google result for the focal NPI and NPI's searching keywords. Here `--input=Data/IndUS2_MD_OD_DF_Keywords.p` is the file contains the NPI and NPI searching keywords; `--start=54000` means that start searching from the `54000`th NPI `--length=30000` means searching next `30000 ` physicians and then stop.
```
python doctor_google_search.py --input=Data/IndUS2_MD_OD_DF_Keywords.p --start=540000 --length=30000
```