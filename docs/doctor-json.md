# Contrato do Doctor

O núcleo público é `omarchy_studio.core.diagnose(host=None) -> dict`. CLI e futuro
Control Center devem consumir esse relatório; os probes não imprimem resultados.
`schema_version: 1` versiona o documento; `readiness.model_version: "0.1"` versiona
os critérios de avaliação independentemente da versão do plugin.

## Campos

| Campo | Conteúdo |
|---|---|
| `schema_version` | versão inteira do envelope JSON |
| `plugin_id`, `plugin_version` | identidade do plugin e versão do núcleo |
| `collected_at` | timestamp UTC de conclusão; a coleta não é atômica |
| `probes.system` | Omarchy, compatibilidade alvo, SO, sessão, arquitetura, kernel |
| `probes.cpu`, `probes.memory` | recursos e observações de desempenho |
| `probes.audio_engine` | pacotes, versões, serviços systemd e ALSA |
| `probes.pipewire` | grafo, metadata, incerteza e visibilidade do servidor |
| `probes.hardware` | placas, correlação de nodes, identidade/driver e PCM ativo |
| `probes.midi` | raw MIDI, clientes/portas sequencer e objetos PipeWire |
| `probes.realtime` | evidência por thread, limites e mecanismos candidatos |
| `probes.configuration` | inventário de caminhos, sem conteúdo ou fusão efetiva |
| `readiness` | pontos confirmados, intervalo, cobertura, estado e dez critérios |
| `advisories` | avisos contextuais e recomendações sem impacto na pontuação |
| `issues` | fonte e tipo de erro de coleta; saída privada de stderr não é incluída |
| `commands` | argv, resultado e exit code dos comandos consultados |
| `privacy` | política resumida de coleta |

O schema de intercâmbio está em `schemas/doctor-v1.schema.json`. Campos de probe
podem ganhar detalhes aditivos; consumidores devem ignorar campos desconhecidos.
Mudanças incompatíveis exigem nova versão de envelope. O schema não substitui os
testes semânticos de pontuação e correlação.

## Entrada e saída padrão

`probes.pipewire.default_nodes` é uma extensão aditiva do envelope v1. Contém
`capture` e `playback`, cada um com `status`, `node_id` e `source`. Relatórios v1
anteriores podem omitir esse objeto. O identificador remete a `probes.pipewire.nodes`
do mesmo snapshot; não é uma identidade persistente de hardware.

| `status` | Significado | `node_id` |
|---|---|---|
| `RESOLVED` | seleção publicada associada a um único node de áudio observado | ID inteiro |
| `UNRESOLVED` | seleção válida, sem correspondência única com um node de áudio identificável | `null` |
| `NOT_SET` | chave de seleção ausente em metadata `default` com permissão explícita de leitura | `null` |
| `UNKNOWN` | servidor/metadata não observado, estrutura inválida ou seleção ambígua | `null` |

A coleta consulta apenas `default.audio.source` e `default.audio.sink`, no subject
inteiro `0` do objeto Metadata chamado `default`. Aceita `Spa:String:JSON` com
objeto `value` ou JSON em string. Preferências `default.configured.*`, outros
subjects e outros namespaces não substituem a seleção atual. O formato segue o
[serializador pw-dump 1.6.8](https://github.com/PipeWire/pipewire/blob/1.6.8/src/tools/pw-dump.c)
e a [publicação de defaults do WirePlumber 0.5.17](https://github.com/PipeWire/wireplumber/blob/0.5.17/src/scripts/default-nodes/apply-default-node.lua).

O nome interno `node.name` serve apenas para correlação em memória: ele pode
conter serial USB e não é incluído no JSON, texto ou erros. O relatório reutiliza
as descrições dos nodes já coletadas. Campos arbitrários de metadata são descartados.

Uma seleção resolvida pode apontar para um dispositivo virtual, monitor de saída
ou node suspenso. O estado descreve a associação da seleção, sem comprovar captura,
reprodução, ligação de uma aplicação ou natureza física. `UNRESOLVED` também pode
ocorrer por hotplug ou visibilidade incompleta; não afirma que o dispositivo foi
desconectado. Um remote alternativo descreve os padrões desse grafo consultado.
As regras existentes de correlação física e o modelo de pontuação 0.1 permanecem.

## Semântica da incerteza

`null` significa UNKNOWN, não zero ou falso. Booleanos distinguem evidência
afirmativa, evidência negativa e ausência de conclusão. `[]` significa nenhum
objeto observado; consulte `scan_complete`, `snapshot_complete` e disponibilidade
do backend antes de concluir ausência real. `support_status: UNKNOWN` é uma
classificação explícita diferente de `status: detected`.

No resultado de comandos: `ok`, `missing`, `failed`, `unavailable`, `timeout`,
`output_limit` e `budget_exhausted`. Falhas nunca são convertidas em texto
estruturalmente vazio tratado como inventário completo. Cada comando tem timeout
de 2 segundos, orçamento compartilhado de 20 segundos e limite de 8 MiB contando
stdout/stderr. Leituras de arquivo têm limite de 2 MiB. O orçamento de comandos
não é prazo rígido para todo acesso ao filesystem.

Probes usam `Host.read/exists/glob/resolve/run/limits`; implementações falsas
podem substituí-los sem acesso a áudio real. O cache é por instância de Host e
deve ser usado em um único diagnóstico: crie outro Host para outro snapshot.

## CLI, privacidade e exportação

```bash
./bin/omarchy-studio doctor --json --verbose
```

stdout contém só JSON. stderr recebe logging de operações em verbose. O relatório
omite seriais e propriedades arbitrárias de clientes; caminhos sob HOME são
redigidos no JSON. Nomes de interfaces/portas ainda podem conter informação
personalizada. Logging verbose pode conter caminhos locais de erro. Nenhum
relatório é enviado ou salvo automaticamente. A UI textual neutraliza caracteres
de controle nas informações externas; consumidores futuros devem tratar strings
como texto e nunca como HTML ou comandos.

Códigos de saída: 0 para relatório produzido, mesmo com problemas; 1 com `--strict`
quando qualquer pré-requisito não passa; 2 para sintaxe de argumentos inválida;
130 para interrupção. `--strict --json` continua emitindo o relatório completo.
Um defeito de programação deve falhar visivelmente, sem ser escondido como
resultado saudável. Não há comandos setup/tune/reset nesta versão.
