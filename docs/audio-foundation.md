# Evidências de áudio e decisões para 0.1

Consulta: 2026-09-09. Referências de software descrevem mecanismos; a versão
instalada em cada computador é sempre coletada, nunca presumida pela data.

## PipeWire e realtime

O [módulo RT do PipeWire](https://docs.pipewire.org/page_module_rt.html) usa
limites adequados de prioridade ou, quando necessário e disponível, Portal
Realtime/RTKit. Portanto `rtkit` ausente, RLIMIT_RTPRIO zero no terminal ou grupo
realtime ausente não provam que o daemon esteja sem scheduling RT. A
[página do pacote Arch](https://archlinux.org/packages/extra/x86_64/pipewire/)
lista rtkit como dependência opcional.

O Doctor lê as políticas por thread em `/proc/<pid>/task/<tid>/stat`, os limites
do próprio processo e limites do daemon. Usa o PID do serviço quando existe;
caso contrário, procura processos `pipewire` do UID atual. Campos vêm da
[documentação procfs do kernel](https://www.kernel.org/doc/html/latest/filesystems/proc.html).
Não solicita promoção de scheduling, não instala realtime-privileges, não executa
mlockall e não exige kernel PREEMPT_RT. Scheduling observado não identifica a
origem do privilégio nem prova a estabilidade do processamento.

A consulta direta à ArchWiki Professional audio foi bloqueada por Anubis nesta
pesquisa; não foi tratada como conteúdo lido. Decisões de implementação se apoiam
na documentação PipeWire/kernel e nos metadados oficiais de pacotes acessíveis.

## Estado configurado e estado medido

[`pw-dump`](https://docs.pipewire.org/page_man_pw-dump_1.html) entrega objetos
JSON, incluindo devices, nodes, ports e metadata. O coletor filtra campos
conhecidos; não depende do alinhamento de `wpctl status` ou `lsusb`.
O [código da versão 1.6.8](https://github.com/PipeWire/pipewire/blob/1.6.8/src/tools/pw-dump.c)
confirma metadata na raiz do objeto e propriedades dos nodes dentro de `info`.

Conforme [pipewire(1)](https://docs.pipewire.org/page_man_pipewire_1.html),
`clock.rate` e `clock.quantum` são defaults; `clock.force-*` são overrides e zero
libera a seleção. Eles não devem aparecer como medições de uma sessão.
[`pw-top`](https://docs.pipewire.org/page_man_pw-top_1.html) distingue drivers e
followers, sugestões e valores atuais, e agrega XRUNs **e outros erros** em ERR.
Não renomear esse contador simplesmente para XRUNs. A versão 0.1 mantém as
medições desconhecidas e não faz parsing de uma tela interativa. Um futuro
ProfilerProbe deverá medir um intervalo e identificar cada driver/workload.

`audio.channels`/`audio.rate` de um node descrevem seu contexto, não a capacidade
máxima de uma interface. `hw_params` de ALSA expõe parâmetros ativos por PCM;
um PCM pode ter muitos canais, portanto contar endpoints não conta inputs.
Nada é aberto ou reconfigurado para testar taxas suportadas.

## Hardware e MIDI

[Procfs ALSA](https://docs.kernel.org/sound/designs/procfile.html) documenta
cards, modules, PCM e hw_params. sysfs relaciona a placa ao dispositivo USB
ancestral; apenas VID, PID, manufacturer e product são selecionados. O driver
vem de modules ou do vínculo sysfs. Não é feita coleta de serial USB.
Dispositivos virtuais e nodes de monitor não contam como interface de captura.
ALSA sequencer pode conter clientes de software e System/Timer; esses nomes
são apresentados como clientes, sem transformar cada um em teclado físico.

USB Audio Class e driver `snd_usb_audio` não provam suporte oficial do fabricante:
quirks, firmware, geração do produto e funções DSP podem mudar o resultado.
Por isso `support_status` inicia em UNKNOWN para todo hardware.

## Configuração e compatibilidade

WirePlumber lê configuração e fragmentos conforme sua
[documentação atual](https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration.html).
O Doctor inventaria caminhos, sem supor que fragmentos Lua antigos de 0.4 sejam
apropriados a 0.5. Não escreve em `/etc`, `/usr/share`, limites PAM, udev, systemd,
sysctl, governors ou configuração de usuário. PipeWire JACK é uma camada de
compatibilidade; instalar ou iniciar jackd paralelo não é pré-requisito.

Pacman é consultado com `-Q`; nenhum refresh de banco ou acesso de rede ocorre.
Chamadas de leitura a serviços/servidor podem estabelecer conexões e ativar
sockets já configurados no sistema. Essa coleta não é um benchmark neutro de
carga: ela dura um intervalo curto e deve ser feita com essa limitação em mente.
