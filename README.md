# rpi_pokedex
 TODO:

    -Scrape type attack bonuses (and maybe weaknesses)
    -Design ERD for database (3NF or STAR)
    -Implement ETL script to transfer to pokemon database
    -Deploy DB on rpi
    -Design rpi zero pokedex GUI that displays pokemon data

# Command list

## lgpio install (needed for 1.3 inch HAT)
```
   wget https://github.com/joan2937/lg/archive/master.zip
   unzip master.zip
   cd lg-master
   sudo make install 
```

## display_and_input install
   pip install -e ./display_and_input
