# Omarchy Studio 0.1 — Foundation

Plugin do Omarchy para construir progressivamente uma estação de produção
musical. A versão 0.1 entrega o **Studio Doctor**, um diagnóstico local sem
alterações de configuração. Integração inicial direcionada ao **Omarchy 4.0.3
(Quattro), x86_64**, pelo sistema oficial de plugins de shell.

**Estado: fundação experimental.** O núcleo e o manifesto têm testes automatizados;
barra em sessão Omarchy, gravação e compatibilidade de hardware ainda precisam
de validação real. O score mede pré-requisitos observados, não qualidade de áudio
nem garantia de uma sessão sem XRUNs.

## Executar o Doctor neste checkout

Requer Linux e Python 3.11+. Não precisa de pip, sudo ou instalação de pacotes.

```bash
./bin/omarchy-studio doctor
./bin/omarchy-studio doctor --json
./bin/omarchy-studio doctor --json --verbose
./bin/omarchy-studio doctor --strict
```

`--json` emite um único objeto; `--verbose` registra as operações em stderr.
Sem gravação automática de logs, upload, telemetria ou criação de diretórios.
Para salvar um diagnóstico por escolha explícita:

```bash
./bin/omarchy-studio doctor --json > doctor-report.json
```

O núcleo também funciona fora do Omarchy para desenvolvimento e coleta parcial;
essa execução não comprova compatibilidade com o plugin gráfico.

## Instalar como plugin do Omarchy

O repositório precisa ter um commit: o gerenciador oficial usa `git clone` e não
copia alterações locais não commitadas. Em uma sessão do Omarchy 4.0.3, execute
a partir do checkout já versionado:

```bash
omarchy plugin validate .
omarchy plugin add "$PWD" --enable
```

O repositório está em [carlosferrerdev/omarchy-studio](https://github.com/carlosferrerdev/omarchy-studio)
e atualmente é privado. Com acesso ao repositório e autenticação SSH configurada,
também é possível instalar diretamente:

```bash
omarchy plugin add git@github.com:carlosferrerdev/omarchy-studio.git --enable
```

O gerenciador mostra as confirmações habituais do Omarchy.

Clique em **Studio** na barra para abrir o Doctor no terminal padrão. O widget
usa `xdg-terminal-exec`, Bash e Python 3.11+, componentes esperados no ambiente
alvo. Ferramentas de coleta ausentes são reportadas; o plugin não as instala.
O manifesto não possui hooks de instalação ou resolução de dependências.

O executável acompanha o plugin; o Omarchy não adiciona seu diretório ao PATH:

```bash
~/.config/omarchy/plugins/carlosferrerdev.omarchy-studio/bin/omarchy-studio doctor --json
```

Gerenciamento pelo menu **Setup > Plugins**, ou pelos comandos oficiais:

```bash
omarchy plugin disable carlosferrerdev.omarchy-studio
omarchy plugin enable carlosferrerdev.omarchy-studio
omarchy plugin update carlosferrerdev.omarchy-studio
omarchy plugin remove carlosferrerdev.omarchy-studio
```

A remoção não precisa desfazer configurações de áudio: 0.1 não as cria.
Veja [ciclo de vida](docs/lifecycle.md) antes de fixar versões ou fazer rollback.

## O que é observado

- Omarchy, versão de pacote, arquitetura, kernel e sessão.
- CPU, topologia disponível, políticas de frequência, governor e memória.
- Pacotes e serviços PipeWire, WirePlumber, compatibilidade PulseAudio/ALSA/JACK.
- Grafo JSON do PipeWire, dispositivos, sources, sinks e metadados de clock.
- Entrada e saída padrão publicadas no PipeWire, com avisos quando a seleção não
  puder ser associada a um node observado ou não estiver publicada.
- Políticas e prioridades por thread do PipeWire, limites do daemon e do Doctor,
  rtkit e pacotes de privilégios, sem tentar conceder realtime.
- Placas ALSA, identidade USB pelo sysfs, driver e parâmetros PCM ativos.
- MIDI raw ALSA, clientes/portas sequencer e portas/nodes MIDI PipeWire.
- Inventário de arquivos PipeWire/WirePlumber sem interpretar fusão de configurações.

`UNKNOWN` em texto e `null` em campos JSON significam ausência de evidência
suficiente. Detectar um dispositivo não comprova suporte oficial ou todos seus
recursos. Sample rate/quantum configurados não são medidas do grafo em execução;
XRUNs, latência de ida e volta e capacidades completas ficam desconhecidos em 0.1.
MIDI e JACK são opcionais para o checklist de captura/reprodução nativa.

A seção **DEFAULT AUDIO** mostra a seleção padrão atual de entrada e saída, com
nome descritivo e estado do node. Esses padrões podem ser diferentes dos
dispositivos escolhidos dentro da DAW. A ausência da informação é `UNKNOWN`;
`NOT_SET` indica chave ausente em metadata com leitura autorizada, e `UNRESOLVED`
indica uma seleção que não pôde ser associada a um único node de áudio na coleta.
Essas observações geram avisos sem alterar a pontuação do checklist.

## Desenvolvimento

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests/unit -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests/integration -v
```

O teste do validador oficial usa `OMARCHY_UPSTREAM` apontando para uma cópia de
leitura do Omarchy 4.0.3; sem ela, somente esse teste é marcado como skipped.
CI fixa o commit oficial e testa Python 3.11–3.14. Não simula um estúdio completo.

```text
manifest.json + BarWidget.qml       integração oficial Omarchy
bin/                               executável e apresentação em terminal
src/omarchy_studio/
  host.py                          acesso ao sistema e limites de execução
  probes/                          coletores substituíveis
  core.py                          relatório compartilhado
  readiness.py                     checklist e recomendações
  cli.py                           apresentação e contrato de saída
tests/{unit,integration,fixtures}/  verificações sem interface física
tests/hardware/                    protocolo manual com equipamento real
```

Documentação: [pesquisa do Omarchy](docs/omarchy-plugin-architecture.md),
[pesquisa de áudio](docs/audio-foundation.md), [score](docs/readiness-score.md),
[contrato JSON](docs/doctor-json.md), [testes](docs/testing.md),
[arquitetura futura e roadmap](docs/roadmap.md), [segurança](SECURITY.md).

Licença [MIT](LICENSE). Projeto comunitário independente; nenhuma afiliação ou
aprovação de fabricantes, do Omarchy ou dos fornecedores de DAWs é reivindicada.
