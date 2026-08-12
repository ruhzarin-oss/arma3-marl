// @HMT_Capteur — addon OBSERVATEUR pour Antistasi Ultimate.
// Ne modifie rien dans le jeu : il lit l'etat et ouvre le pont TCP vers Python.
// Charge en -serverMod, donc Antistasi reste strictement vanilla.
class CfgPatches
{
    class HMT_Capteur
    {
        units[] = {};
        weapons[] = {};
        requiredVersion = 0.1;
        requiredAddons[] = {"A3_Functions_F"};
        author = "Harmattan";
        version = "1.0";
    };
};

class CfgFunctions
{
    class HMT
    {
        class capteur
        {
            file = "hmt\capteur\fn";
            class postInit { postInit = 1; };
        };
    };
};
