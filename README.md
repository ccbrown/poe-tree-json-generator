How to use:

1. You need some game files: Data/PassiveSkills.csv, Data/Stats.csv, Metadata/PassiveSkillGraph.psg, Metadata/passive_skill_stat_descriptions.txt, and Metadata/stat_descriptions.txt. Drop them into the directory alongside generator.py. You can extract these using tools such as found here: https://github.com/MuxaJIbI4/libggpk
2. The generator only generates the "root", "groups", and "nodes" properties of the tree. You need to copy the rest from the current skill tree and place it into a file named merge.json in the directory.
3. Compile boost-formatter.cpp to an executable named boost-formatter.
4. Run `./generator.py`.
