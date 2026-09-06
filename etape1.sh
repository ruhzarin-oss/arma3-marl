cd /home/younes/arma3-marl
exec > etape1.log 2>&1
echo "debut $(date +%H:%M:%S)"
./.venv/bin/python -u controle_canal.py
echo "code de sortie : $?"
echo "fini $(date +%H:%M:%S)"
