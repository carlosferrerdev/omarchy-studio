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
