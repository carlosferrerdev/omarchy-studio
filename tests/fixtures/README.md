# Fixtures

Dados **sintéticos**, sem captura de hardware real ou alegação de suporte.
`pipewire.json` reproduz as formas Core, Metadata, Client, Device, Node e Port
do [pw-dump 1.6.8](https://github.com/PipeWire/pipewire/blob/1.6.8/src/tools/pw-dump.c).
Os objetos fictícios têm identidades cruzadas para testar a correlação.
O serial sentinela serve para comprovar que dados não permitidos são descartados.

`tests/fakes.py` fornece pacotes, serviços, procfs, sysfs e scheduling simulados.
Snapshots reais futuros devem remover seriais, nomes pessoais e identificadores
de projetos, registrar versões de origem e indicar a autorização para publicação.
