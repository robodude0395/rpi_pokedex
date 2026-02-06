# RPI pokedex

# Intro
So a while ago I got an rpi zero (basically a mini linux computer) and I was stuck on a question: "What can project could I do to showcase all my newfound knowledge in web-scraping and SQL?"... Then it struck me!

*An rpi pokedex!*

![image](images/pokedex.png)

# The software
The software consist of a bunch of ETL scripts that do the following:

1. Scrape pokedex data from (100% not bulbapedia)
2. Load the data locally as a bunch of json files and png files
3. Transform the data to fit the modelled ERD diagram
4. Load the transformed data onto a local serverless sqlite database for later querying

After the data is loaded, a script runs that is basically my take on what a pokedex designed in a distant apocalyptic future would look like (GUI design from scratch is hard! ok?).

# The hardware
If you were to see the actual pokedex you'd think that this is some arcane device Tony Stark made in a cave with a box of scraps. Alas... This is the product of my dedication and overzealous use of hot glue.

The hardware consists of:

+ Rpi zero W as the main brain
+ A screen+joystick HAT for peripheral use
+ A discarded Vape battery I gutted and added my electronics onto for portability and recharging
+ An ADC module for battery level monitoring

![image](images/pokedex.png)

Is this the prettiest product? No.
Is it the safest? I wouldn't bet on it
Does it look cool? It does to me!

# DISCLAIMER
This is very much a passion project that I'm tackling in my spare time. A lot of the codebase still needs polishing and implementing.

The webscraping and GUI basics are pretty much done but the database setup and loading still need work.


