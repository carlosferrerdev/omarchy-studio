# Roadmap e contratos futuros

Entregável atual: **0.1 Foundation / Studio Doctor**. A arquitetura de plugin
foi pesquisada; diagnóstico inicial existe; testes de sessão Omarchy e hardware
são um gate aberto. A implementação do Doctor não significa que toda a fase de
fundação de áudio, tuning ou instalação de software esteja concluída.

## Curto prazo — Linux nativo

| Fase | Entrega | Gate de saída |
|---|---|---|
| 0 | Pesquisa e contrato oficial de plugin | manifesto, evidências, ciclo de vida revisados |
| 1 | Audio Foundation | baseline Linux nativa validada sem conflitos com Omarchy |
| 2 | Hardware Detection | correlação ALSA/sysfs/PipeWire e fixtures reais sanitizadas |
| 3 | Studio Doctor | robustez, incerteza, documentação e teste em máquinas Omarchy |
| 4 | Audio Tuning | planos reversíveis, backup, restauração e medição antes/depois |
| 5 | DAWs Linux | instalação legítima e testes por versão: REAPER, Bitwig, Ardour, Mixbus, Renoise |
| 6 | Plugins Linux | descoberta LV2/VST2/VST3/CLAP e sessões reais com hosts escolhidos |

O resultado esperado dessas fases é a estação Linux nativa funcional. O Doctor
fornece evidência para elas, sem instalar DAWs, plugins ou aplicar tuning em 0.1.

Incremento do Doctor neste checkout: entrada e saída padrão do PipeWire aparecem
no texto e no JSON, com estados explícitos de incerteza e avisos sem impacto no
score. Há cobertura sintética para seleção atual versus preferência salva,
metadata inacessível/malformada, ambiguidades e privacidade dos nomes internos.
A validação em sessão Omarchy e hardware real continua pendente.

## Médio prazo — compatibilidade medida

| Fase | Entrega planejada |
|---|---|
| 7 | Wine Audio Laboratory |
| 8 | yabridge |
| 9 | Windows VST/VST3/CLAP, somente quando bridge/formato forem viáveis |
| 10 | Wine Prefix Management |
| 11 | Plugin Compatibility Profiles |
| 12 | StudioDB |
| 13 | Windows DAW Laboratory |

Wine terá runtime identificado por versão/hash, prefixos isolados por perfil,
versão do bridge, arquitetura, fontes oficiais e testes de atualização em cópia.
O runtime do projeto não dependerá silenciosamente da versão global de Wine do
Arch: atualizar o sistema não deve migrar irreversivelmente o ambiente de uma
sessão aprovada. Prefixos e installers legítimos continuam dados do usuário.
Qualquer estratégia de pin precisa de manutenção e atualização de segurança,
não congelamento indefinido. Nenhum download, prefixo, bridge ou Wine foi criado.

Ableton Live, FL Studio, Fender Studio Pro, Studio One, Cubase e Cakewalk serão
candidatos de laboratório **UNKNOWN** até testes por versão. A matriz precisa
distinguir instalar, abrir, autorizar, gravar, reproduzir, salvar/reabrir e carregar
plugins. Abrir a janela não basta para declarar compatibilidade. Não haverá
redistribuição de binários comerciais, firmware sem autorização, licenças ou DRM
contornado. Links e installers deverão ser oficiais e de uso legítimo.

## Longo prazo — ecossistema

| Fase | Entrega planejada |
|---|---|
| 14 | Omarchy Studio Control Center, consumidor do mesmo núcleo/JSON |
| 15 | Hardware Compatibility Database |
| 16 | Automated Hardware Profiles |
| 17 | Professional Studio Benchmark |
| 18 | Vendor Partnerships |
| 19 | Native Linux advocacy |

Focusrite, Universal Audio, RME, MOTU, Audient, PreSonus, Behringer, SSL,
Native Instruments, IK Multimedia, Line 6, Fender, Neural DSP, Arturia e outras
marcas são candidatas a estudo, sem alegação de suporte ou parceria. O mesmo vale
para Ableton, Image-Line e Steinberg na discussão do ecossistema de software.

## Módulos planejados

```text
Omarchy shell / gerenciador oficial
  └── Omarchy Studio (manifesto + QML)
       ├── Core de diagnóstico ── CLI / JSON / futura GUI
       │    ├── System / CPU / Memory
       │    ├── PipeWire / ALSA / USB / MIDI
       │    └── Realtime / futuras medições
       ├── Planner → executor de mudanças → diário / backup / restore
       ├── Catálogos DAWs e plugins nativos
       └── Laboratório isolado → perfis → evidências StudioDB
```

Processos externos e arquivos ficam atrás de `Host`. Probes recebem dependências
por injeção. Políticas do score não vivem na UI. Futuro executor de mudanças terá
interfaces e privilégios separados; nenhum `collect()` poderá virar uma mutação.
Hotplug exigirá correlacionar IDs efêmeros por snapshot, sem usar número de card
ALSA como identidade persistente universal.

## Modos de áudio — hipóteses para teste

| Rótulo futuro | Quantum candidato |
|---|---:|
| SAFE | 512 |
| MIXING | 256 |
| RECORDING | 128 |
| LOW LATENCY | 64 |
| ULTRA LOW LATENCY | 32 |

São candidatos, não presets aplicáveis em 0.1 ou valores universalmente seguros.
O futuro perfil incluirá rate, limites do dispositivo, workload e evidências de
XRUNs/latência. `quantum / rate` é duração de um ciclo, não latência total de ida
e volta. Reduzir quantum precisa de medição e rollback; não concede pontos extras.

## Vocabulário de compatibilidade

| Classificação | Evidência exigida |
|---|---|
| OFFICIALLY SUPPORTED | declaração verificável do fabricante, produto/versão/plataforma exatos |
| NATIVE | componente executa diretamente em Linux; não implica suporte oficial |
| CLASS COMPLIANT | evidência do protocolo/classe para modelo e modo, não apenas VID/PID |
| COMMUNITY SUPPORTED | implementação/testes comunitários documentados, com limitações |
| COMPATIBILITY LAYER | Wine/bridge ou outra camada explicitamente identificada |
| EXPERIMENTAL | laboratório incompleto, instável ou insuficientemente reproduzido |
| UNSUPPORTED | incompatibilidade conhecida, documentada e delimitada |
| UNKNOWN | evidência ausente, insuficiente ou ainda não revisada |

Essas dimensões podem coexistir: um aplicativo NATIVE pode não ter suporte oficial
do fornecedor, e uma interface class compliant pode precisar de suporte comunitário
para mixer/DSP. StudioDB deverá separar declarações do fabricante, mecanismo de
execução e resultados de teste, em vez de forçar tudo em um único booleano.
Em 0.1 cada dispositivo tem `status: detected` independente de `support_status:
UNKNOWN`. Uma observação de driver nunca promove automaticamente esse status.

Cada registro futuro terá produto, revisão/firmware, versões do stack, arquitetura,
data, fontes, resultados por função, taxas/quantums testados, duração, limitações,
reprodução e expiração/reteste. Não existe hoje matriz de compatibilidade aprovada.
