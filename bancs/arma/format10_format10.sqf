// format10.sqf — `format` de SQF gere-t-il DIX arguments ?
// La sonde du temoin en passait dix et lisait `autoc|true` la ou une mesure pas-a-pas
// lit `false`. Si %10 est mal analyse, les champs se decalent et ma lecture etait fausse.
HMT_LOG = { diag_log _this };
[] spawn {
    sleep 3;
    "HMT|FM|debut" call HMT_LOG;
    (format ["HMT|FM|neuf|a|%1|b|%2|c|%3|d|%4|e|%5|f|%6|g|%7|h|%8|i|%9",
             "A","B","C","D","E","F","G","H","I"]) call HMT_LOG;
    (format ["HMT|FM|dix|a|%1|b|%2|c|%3|d|%4|e|%5|f|%6|g|%7|h|%8|i|%9|j|%10",
             "A","B","C","D","E","F","G","H","I","J"]) call HMT_LOG;
    // et la forme EXACTE de la sonde du temoin
    (format ["HMT|FM|sonde|%1|arme|%2|coups|%3|metres|%4|hauteur|%5|pente|%6|fsm|%7|autoc|%8|path|%9|groupe|%10",
             "NOM","oui",13,14,130,0.46,false,false,true,1]) call HMT_LOG;
    "HMT|FM|TERMINE" call HMT_LOG;
};
