
# Collecting the Profiles

```shell
cd PhysicianReview/doctor_reviews/
mkdir Output
```


## Run HealthGrades

The following command means: reading the NPI-Keywords information from `--input=Data/healthgrades/healthgrades_v1.p`, start from the number `start=50000`, and collecting the next `length=10000`, save the information every `chunk=100` physicians into a file.


```shell
python doctor_healthgrades.py --input=Data/healthgrades/healthgrades_v1.p --start=0 --chunk=100
```

## Run Vitals
Same to `HealthGrades`.

```shell
python doctor_vitals.py --input=Data/vitals/vitals_v1.p --start=50000 --length=10000 --chunk=100
```


## Run RateMD

The following command has the same pattern as `HealthGrades`. The different is that you can add `--proxyapi=XXXXX` to use the API keys from [ScrapyAPI](https://www.scraperapi.com/) to escrape the `Cloudflare`'s detection.

```shell
python doctor_ratemds.py --input=Data/ratemds/ratemds_v1.p --start=10000 --length=10000 --chunk=100 --proxyapi=XXXXXXX
```

## Run Yelp

Same to `RateMDs`.

```shell
cd PhysicianReview/doctor_reviews/
mkdir Output
python doctor_yelp.py --input=Data/yelp/yelp_v1.p  --start=0 --chunk=100
```

## Run ZocDoc

Same to `RateMDs`.

```
python doctor_zocdoc.py --input=Data/zocdoc/zocdoc_v1.p --start=7000 --length=3000 --chunk=100 --proxyapi=XXXXXXX
```


