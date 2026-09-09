# Arquitetura de plugins do Omarchy — pesquisa para Studio 0.1

Pesquisa realizada em **2026-09-09, antes da implementação**. Este documento
separa o contrato observado no upstream das decisões do Omarchy Studio.

## Base verificada

O site oficial aponta para [omacom/omarchy](https://github.com/omacom/omarchy).
O endereço histórico `basecamp/omarchy` redireciona para essa organização.
A release mais recente consultada é
[v4.0.3](https://github.com/omacom/omarchy/releases/tag/v4.0.3), de 8 de setembro
de 2026, commit `0534987009061cbe2dacdde4ad564092ab698d12`.
Uma cópia de leitura dessa tag foi examinada fora deste projeto; não há fork
nem código do sistema Omarchy incorporado ao produto.

O Omarchy 4 (Quattro) substituiu o shell anterior por um processo Quickshell
persistente. Há uma arquitetura oficial de plugins. Referências primárias:

- [Manual: Shell Plugins](https://omarchy.org/manual/shell-plugins/).
- [Contrato do shell na tag pesquisada](https://github.com/omacom/omarchy/blob/v4.0.3/shell/README.md).
- [Registro e validação em QML](https://github.com/omacom/omarchy/blob/v4.0.3/shell/services/PluginRegistry.qml).
- [Validador CLI](https://github.com/omacom/omarchy/blob/v4.0.3/bin/omarchy-plugin-validate).
- [Catálogo de plugins incluídos](https://github.com/omacom/omarchy/blob/v4.0.3/shell/plugins/README.md).
- [Guia de desenvolvimento](https://plugins.omarchy.org/develop.html).

## Contrato observado

Um repositório Git contém `manifest.json` na raiz e os componentes QML locais.
O manifesto usa `schemaVersion: 1`, `id`, `name`, `version`, `kinds` e
`entryPoints`. Os tipos conhecidos são `bar-widget`, `panel`, `overlay`,
`menu`, `service` e `bar`; a chave de entrada de `bar-widget` é `barWidget`.
IDs de terceiros não podem usar o namespace reservado `omarchy.*`.
Entradas precisam ser caminhos relativos existentes, sem `..`; o validador
também rejeita links simbólicos dentro do plugin (exceto internos de `.git`).
Não há campos contratuais de resolução de pacotes, migrações de áudio ou uma
API de extensões Python. Campos extras não constituem novas capacidades do host.

Plugins próprios ficam em `$OMARCHY_PATH/shell/plugins/`; os de terceiros em
`~/.config/omarchy/plugins/<id>/`. Os comandos desta tag usam esse caminho
literal sob HOME, mesmo quando XDG_CONFIG_HOME aponta para outro lugar.
O shell controla a habilitação e o layout em `~/.config/omarchy/shell.json`.
Um widget habilitado ocupa uma posição da barra; `barWidget.defaultSection`
define a posição inicial. Alterações no código provocam recarga automática.

Os componentes recebem propriedades conforme o tipo. Widgets usam `qs.Ui`
(`BarWidget`, `WidgetButton`) e o tema compartilhado. O Omarchy 4.0.3 limita
as fachadas QML entregues a terceiros; acesso irrestrito a serviços internos
não é contrato público. Plugins continuam executando como código do usuário
no processo do shell. Não existe isolamento de segurança equivalente a sandbox.

O IPC oficial usa `omarchy-shell shell ...`; não se inicia outro Quickshell.
Menus de gerenciamento existem em **Setup > Plugins**. A extensão de menu em
`~/.config/omarchy/extensions/omarchy-menu.jsonc` é um arquivo compartilhado;
o Studio 0.1 não precisa modificá-lo para disponibilizar sua ação na barra.

## Instalação, atualização e remoção

- [add](https://github.com/omacom/omarchy/blob/v4.0.3/bin/omarchy-plugin-add):
  `omarchy plugin add <git-url-ou-repositório-local> --enable` faz staging,
  validação, verificação de colisão de ID, instalação e ativação por IPC.
  Há confirmação interativa; `--yes` é a opção explícita de automação.
  Não executa código do plugin, install hooks ou sudo.
- [update](https://github.com/omacom/omarchy/blob/v4.0.3/bin/omarchy-plugin-update):
  busca `origin HEAD`, mostra diff para confirmação, tenta fast-forward e
  valida novamente. Falha de validação restaura ORIG_HEAD. Não é um resolvedor
  SemVer e não valida o comportamento do Python/QML. Não se deve supor que uma
  tag em detached HEAD constitui pin permanente contra esse comando.
- [remove](https://github.com/omacom/omarchy/blob/v4.0.3/bin/omarchy-plugin-remove):
  desabilita e remove checkout Git; diretórios manuais têm tratamento de backup,
  e links externos têm tratamento próprio. Não há uninstall hook do Studio.
- Pin, troca de branch e rollback de código são operações Git explícitas,
  com o plugin desabilitado e alterações locais preservadas. Não executar
  atualizações globais de plugins quando uma revisão precisa permanecer fixa.

## Referências de implementação

O [widget de relógio](https://github.com/omacom/omarchy/blob/v4.0.3/shell/plugins/panels/clock/BarWidget.qml)
e [BarWidget base](https://github.com/omacom/omarchy/blob/v4.0.3/shell/Ui/BarWidget.qml)
mostram a integração de barra. O serviço de bateria e os painéis de diagnóstico
mostram separação de lógica e uso de `Quickshell.Io.Process`.
O [plugin Basecamp](https://github.com/basecamp/omarchy-basecamp-plugin)
é uma referência externa mantida pela 37signals: QML chama um CLI separado,
documenta dependências e usa o ciclo oficial de plugins. Isso comprova o padrão
de composição; não implica endosso do Studio nem dependência do Basecamp.

## Decisões para 0.1

1. Plugin real com ID `carlosferrerdev.omarchy-studio`, manifesto v1 e um widget
   pequeno. Clicar em **Studio** abre o Doctor no terminal padrão pelo
   `xdg-terminal-exec`, com argumentos separados. Nenhum diagnóstico periódico
   ou serviço adicional permanece ativo durante gravações.
2. Núcleo Python 3.11+ somente com biblioteca padrão, dentro do mesmo checkout.
   `bin/omarchy-studio doctor [--json] [--verbose]` é uma interface do Studio,
   **não** uma API inventada para o Omarchy. O instalador não adiciona seu `bin`
   ao PATH; a barra usa caminho resolvido relativo ao próprio componente.
3. CLI → coleta estruturada → avaliação → apresentação. Uma GUI futura poderá
   consumir o mesmo JSON sem repetir probes ou critérios de score.
4. Apenas observação nesta versão: nenhum pacote instalado, arquivo de áudio
   alterado, serviço reiniciado, dispositivo aberto para gravação ou privilégio
   realtime concedido. Dependências ausentes viram evidências no relatório.
5. Alvo inicial de integração: **Omarchy 4.0.3**, Linux x86_64, manifesto v1.
   3.x é incompatível com esta integração; versões diferentes, builds dev e
   arquiteturas não verificadas são explicitamente não validadas. O núcleo
   ainda pode produzir diagnóstico parcial fora do Omarchy.
6. O gerenciador oficial é dono da instalação e do estado da barra. Os diretórios
   próprios futuros seguem XDG; o Doctor não cria estado persistente por padrão.

## Compatibilidade e limites da validação

Este contrato é recente e evolui (inclusive as fachadas de segurança em 4.0.3).
Referências estão fixadas por tag/commit; CI deve executar o validador oficial
nessa revisão e os testes do núcleo. Novas versões exigem revisão de manifesto,
imports `qs.Ui`, launcher e ciclo de vida, seguida de teste em sessão gráfica.
Não declarar suporte a toda versão futura só por aceitar `schemaVersion: 1`.

O ambiente de desenvolvimento inspecionado é Ubuntu 26.04.1, sem Omarchy ou
Quickshell. Validação estática e testes simulados não comprovam funcionamento da
barra, permissões realtime ou gravação em hardware. Esses gates ficam na suíte
manual documentada em `docs/testing.md`; suporte de hardware começa em UNKNOWN.
