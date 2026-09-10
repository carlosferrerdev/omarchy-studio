# Studio Readiness — modelo 0.1

O número representa **cobertura confirmada de um checklist de fundação para
captura e reprodução Linux nativas**. Não é benchmark, probabilidade de sucesso,
nota de um fabricante ou estimativa de latência. Pesos de desempenho não foram
inventados: são dez verificações binárias de igual peso (10 pontos cada).

Dar o mesmo peso a cada verificação torna a conta a porcentagem de requisitos
confirmados. Essa escolha é uma política explícita de produto, não uma calibração
empírica de importância. Todos precisam passar para o status máximo; nenhuma
verificação crítica pode ser compensada por CPU rápida ou RAM abundante.
Hardware ALSA e nodes PipeWire são camadas distintas: a presença do endpoint do
kernel não assegura sua exposição no grafo.

## Métricas e critérios exatos

| ID | Peso | PASS | FAIL conhecido / UNKNOWN |
|---|---:|---|---|
| `omarchy_target` | 10 | pacote Omarchy estável 4.0.3, x86_64 | Omarchy não detectado ou anterior a 4: FAIL; versão dev, outra versão/arquitetura: UNKNOWN |
| `linux` | 10 | uname identifica Linux | outro sistema: FAIL |
| `pipewire` | 10 | `pw-dump` válido expõe Core | pacote e ferramenta ausentes com serviço inativo: FAIL; falha/timeout/JSON inválido/acesso insuficiente: UNKNOWN |
| `wireplumber` | 10 | Client WirePlumber visível no dump | dump completo sem cliente e serviço inactive/failed: FAIL; demais ausências: UNKNOWN |
| `alsa` | 10 | `/proc/asound` existe | ausente: FAIL; permissão/erro de leitura de metadados: UNKNOWN |
| `pcm_capture` | 10 | pelo menos um `pcm*c` de placa física | inventário completo sem endpoint: FAIL; inventário incompleto/placa de natureza desconhecida: UNKNOWN |
| `pcm_playback` | 10 | pelo menos um `pcm*p` de placa física | mesmo tratamento de captura |
| `graph_capture` | 10 | Audio/Source correlacionado a placa física, estado suspended/idle/running | inventários completos sem node elegível: FAIL; inventário incompleto ou remote alternativo: UNKNOWN |
| `graph_playback` | 10 | Audio/Sink correlacionado a placa física, estado suspended/idle/running | mesmo tratamento de captura |
| `realtime` | 10 | thread do daemon PipeWire do usuário em FIFO/RR com prioridade > 0 | threads legíveis e nenhuma RT: FAIL; processo/threads inacessíveis, snapshot incompleto: UNKNOWN |

Os nomes dos pacotes são observações do pacman. Uma ferramenta ausente não prova
que seu daemon esteja ausente. PID e UID são conferidos; não basta olhar a thread
principal do PipeWire. O mecanismo que concedeu realtime continua UNKNOWN, mesmo
quando uma thread RT foi vista. `snd_aloop`, `snd_dummy` e caminhos sysfs virtuais
não recebem os pontos de interface física. Estados suspended/idle são normais
em dispositivos ociosos e não causam reprovação.

O estado de cada item e a referência à evidência aparecem no próprio JSON.
Os predicados executáveis estão em `src/omarchy_studio/readiness.py`.

## Fórmula e estados

```text
score = soma dos pesos de PASS
unknown_weight = soma dos pesos de UNKNOWN
possible_score = score + unknown_weight
coverage_percent = 100 - unknown_weight
```

O denominador permanece 100 quando falta uma ferramenta. Nunca renormalizar
90 pontos conhecidos para uma nota 100 removendo o requisito desconhecido.

- Qualquer FAIL → `NEEDS_ATTENTION`.
- Sem FAIL, com UNKNOWN → `INCOMPLETE`.
- Dez PASS → `FOUNDATION_CHECKS_PASSED`.

Exemplos: dez PASS = 100, cobertura 100%; nove PASS + RT desconhecido = intervalo
90–100, cobertura 90%, INCOMPLETE; nove PASS + RT não observado em todas as threads
legíveis = 90, cobertura 100%, NEEDS_ATTENTION. JACK ausente não muda esses números.

## Fora da pontuação

CPU, frequência, RAM, swap, MIDI, rtkit e camadas opcionais são evidências e
avisos. RAM disponível abaixo de 10% gera um aviso operacional explícito;
não é requisito mínimo de uma DAW. `powersave`/`conservative` pedem medição,
sem assumir que `intel_pstate` precise de governor performance. Não se exige
kernel RT, rtkit, grupo realtime, memlock ilimitado ou pipewire-jack para todos.

Os padrões de entrada/saída em `pipewire.default_nodes` são observações adicionais.
Seleção não publicada ou sem correspondência única gera aviso, sem penalizar o
score: aplicações podem escolher seus próprios dispositivos. A resolução de um
padrão virtual ou de um monitor também não concede pontos de hardware físico.

## Limitações e evolução

O snapshot não mede carga DSP, estabilidade USB, drift entre interfaces, latência
real, isolamento acústico, qualidade de conversores, DAWs, licenças ou reprodução
simultânea com captura. As verificações podem passar em placas diferentes;
sincronização e operação duplex não foram provadas. Algumas permissões só podem
ser demonstradas abrindo o dispositivo, operação fora deste diagnóstico.

Mesmo 100 pontos **não** produz READY FOR RECORDING. A próxima etapa precisa de
testes reais de workload, duração, taxa de XRUNs e latência, com consentimento para
emitir/capturar áudio. Qualquer alteração de pesos ou critérios exige incremento
de `model_version`, exemplos atualizados e regressões. Notas de modelos diferentes
não devem ser comparadas diretamente.
