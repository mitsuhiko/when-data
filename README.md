# when-data

This contains timezone mapping information for [when](https://github.com/mitsuhiko/when)
preprocessed from the geonames data.  It exists in a separate repository so that one does
not need to download directly from geonames megabytes of data adding load to that service.

To update the data here:

```
make
```

The final processed data ends up in `locations.txt`.
