# mammals_stars

Wandrille's mammal points and my script to transform these to star assets and
labels.

The program:

    usage: csv_to_openspace.py [-h] -i INPUT_DATASET_CSV_FILE -c CACHE_DIR -a ASSET_DIR [-v]

    Process input CSV files for OpenSpace.

    options:
    -h, --help            show this help message and exit
    -i INPUT_DATASET_CSV_FILE, --input_dataset_csv_file INPUT_DATASET_CSV_FILE
                            Input dataset CSV file.
    -c CACHE_DIR, --cache_dir CACHE_DIR
                            OpenSpace cache directory.
    -a ASSET_DIR, --asset_dir ASSET_DIR
                            Output directory for assets.
    -v, --verbose         Verbose output.

The input CSV file tells the program what to do. In each dir (mammals_families_species
and mammals_families_orders_species), take a look at the [...]_dataset.csv file.
Each line tells the program which data csv file to load and what to do with it, 
either turn it into stars or labels. If stars, there are a bunch of parameters
to tweak star appearance, and also an option to set an asset name for fading. (This
is a little complicated, just ask me.)

The cache dir is cleaned out automatically, you need to provide its location
on your setup.

The asset dir is where you want the assets placed when run.

Example run:

First `cd` into the data dir, then run:

`../csv_to_openspace.py -i mammals_families_species_dataset.csv -c /mnt/e/OpenSpace/user/cache -a /mnt/e/OpenSpace/user/data/assets/mammals_families_species_stars`

Then make sure your profile is set up to load the new assets.
