# Cities: Skylines Urban Road

Cities: Skylines Urban Road (CSUR) is a fully modular road asset framework for Cities: Skylines created by procedural content generation and asset packaging.

CSUR has been released onto [the Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=1959216109). The [CSUR Official Website](https://csur.fun) is also under construction. **Complete API documentation and model/texture specification for procedual generation will follow soon.** 

![Ground road lineup](https://github.com/victoriacity/CSUR/blob/master/render.png)

## Motivation

In the past 4 years, *Cities: Skylines* has almost dominated the city-building genre on the PC platform by providing outstanding features and engaging gameplay with more than 5 million copies sold. Another critical reason why *Cities: Skylines* has enjoyed such popularity is that it provides extensive support for community-contributed game assets and mods (plug-in code libraries). *Cities: Skylines* is also one of the games with the largest amount of community contents on the Steam Workshop.

Roads are one of the most important types of urban infrastructure and plays a key role in almost any city-building game. Nevertheless, due to performance optimization and balancing the depth of multiple aspects of city simulation, roads in the base game of *Cities: Skylines* are created in a relatively simplistic manner, omitting all markings at highway ramps and lane transitions (i,e., addition or reduction of a lane). This has motivated enthusiastic *Cities: Skylines* players to add details to roads in their city builds using community-constributed assets and mods. A highlight among such efforts was the original [CSUE](https://steamcommunity.com/workshop/filedetails/?id=1423096565)/[CSUR](https://steamcommunity.com/workshop/filedetails/?id=1206133771) road asset packs created by AmamIya. The key idea of these asset packs was to make different combinations of ramps and lane transitions into draggable road segment modules instead of treating them as intersections as in the base game. This allows all road markings to be modeled in each module and greatly increases the realism of road infrastructure in *Cities: Skylines*.

Originally, all game assets in CSUE/CSUR were modeled and textured manually with hundreds of hours spent on creating 3D models and packaging them using the Asset Editor interface of the game. By leveraging procedural content generation and automatic asset packaging, the consistency of quality in assets and efficiency can be improved at an unprecedented scale. For example, the 2000-asset package done by the current CSUR code should have taken several years to be created manually. This has led to the development of the CSUR software suite in this repository.

Being the largest road content collection ever created for the game, we believe that CSUR will make a profound influence on the *Cities: Skylines* community. Although developed for *Cities: Skylines*, application of CSUR may have a broader picture. With the flexibility and realism in simulated road infrastructure delivered by CSUR, it also has the potential to create procedually-generated simulation environments involving urban roads, such as synthetic data to train machine learning systems for autonomous vehicles.

## Methods
Initially, the definition of road variations (e.g., number of lanes, whether it is a ramp or a transition) and enumeration of possible road combinations were written in Python. Thus, Blender (version 2.80) was used to procedually generate road models based on elementary components of road networks (see our [RoadElements](https://github.com/citiesskylines-csur/RoadElements) repository) because of its extensive Python scripting support. The Cairo graphics libary with Python interface was used to provide visualization of road combinations as thumbnails in the game. The CSUR Python program contained in this repository also generates the prefab parameters and metadata to be packaged in the game. To automatically perform asset packaging in the game, a plug-in (called Mod in *Cities: Skylines* community) was also developed using the Unity Engine and the game's own API to run in the Asset Editor. ([Source code](https://github.com/citiesskylines-csur/RoadImporter)) 


