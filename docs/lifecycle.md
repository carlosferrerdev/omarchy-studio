# Ciclo de vida, XDG e reversibilidade

## Implementado em 0.1

Instalação, enable/disable, update e remove pertencem ao gerenciador oficial do
Omarchy. O plugin ocupa apenas seu checkout e sua entrada de barra gerenciada
pelo host. Não há install hooks, pacotes instalados pelo Studio, backup de áudio
necessário, serviço Studio, diário de mutações ou migração de configuração.
Doctor tem o mesmo efeito em execuções repetidas: coletar; números e timestamps
podem variar com o estado real. Não cria bytecode Python pelo executável local.

O formato de código é versionado em manifesto/Python. Uma instalação por Git
precisa conter os arquivos commitados. A atualização oficial segue o HEAD remoto,
não um catálogo de releases SemVer. Ela valida estrutura, não segurança ou áudio.
Revise o diff e não force atualização sobre trabalho local.

Rollback de código: desabilite o plugin pelo comando oficial; preserve o checkout
e alterações locais; escolha uma revisão conhecida com as ferramentas Git; valide
o diretório; reabilite e teste. Não rode o update oficial até decidir abandonar
esse pin. Não há comando Studio rollback em 0.1 nem promessa de rollback
transacional do shell do Omarchy. Prefira experimentar releases com usuário de
teste e manter anotada a revisão anterior.

Uninstall usa `omarchy plugin remove carlosferrerdev.omarchy-studio`. Arquivos de
relatório que o usuário salvou fora do checkout continuam pertencendo ao usuário.
Reset do Doctor não é necessário: não há configuração própria persistida.

## Plano para Studio Setup — não implementado

O futuro Setup será uma operação separada, acionada explicitamente; nunca um
efeito de habilitar o widget, abrir o Doctor ou atualizar o código. Sequência:

1. Coletar diagnóstico e pré-condições, verificar versões e mudanças concorrentes.
2. Produzir plano com identificador, operações, motivo, risco e diff; `--dry-run`
   entrega o mesmo plano sem efetivá-lo nem requerer root.
3. Confirmar o plano quando necessário, por operação privilegiada bem delimitada.
4. Adquirir lock de mutação, revalidar hashes e preservar original/metadata antes
   de qualquer escrita. Criar backup local restrito.
5. Aplicar arquivos próprios por escrita temporária + rename atômico; registrar
   cada etapa, verificar saúde e oferecer restauração se houver falha.
6. Registrar sucesso, falha ou recuperação pendente. Retomar com segurança depois
   de crash, sem tratar um diário incompleto como instalação concluída.

Nada disso é campo ou hook oficial do manifesto. Será um executor próprio,
separado do diagnóstico, com um helper privilegiado mínimo para cada ação que
precisar de root; jamais todo o aplicativo elevado.

## Registro de propriedade planejado

O diário deverá conter `transaction_id`, versão do Studio, estado da operação,
precondições, hashes antes/depois, origem e caminho do backup, permissões/dono,
pacotes já presentes, pacotes adicionados e motivo. Cada arquivo terá classe
`preexisting_unmodified`, `created_by_studio` ou `modified_with_backup`.

Uninstall/reset futuros deverão mostrar o plano inverso. Um arquivo criado só
poderá ser removido automaticamente se o hash ainda for o gravado pelo Studio.
Configuração alterada só poderá ser restaurada sem conflito se seu conteúdo
atual não tiver mudanças posteriores. Caso contrário, preservar ambos e pedir
resolução; não apagar o trabalho do usuário.

Pacotes não serão removidos em cascata por terem aparecido no diário. A origem
de instalação é evidência histórica, não autorização de remoção. Dependências
atuais, instalação explícita posterior e outros consumidores precisam ser
verificados; a política conservadora será mantê-los, com remoção opcional
confirmada separadamente. Snapshots completos não substituem backups por arquivo.

O gerenciador do Omarchy não possui uninstall hook para executar essa reversão.
Antes de oferecer mutações, o projeto precisará entregar `reset/restore` explícito
e instruções de recuperação que sobrevivam à exclusão do plugin, dentro de STATE
com formato documentado. A remoção direta do checkout deverá continuar segura.

## Diretórios

O [XDG Base Directory](https://specifications.freedesktop.org/basedir/latest/)
define configuração, dados, estado e cache com propósitos distintos:

| Conteúdo | Local próprio planejado |
|---|---|
| Preferências, perfis selecionados | `$XDG_CONFIG_HOME/omarchy-studio/` |
| StudioDB e recursos versionados | `$XDG_DATA_HOME/omarchy-studio/` |
| Diário, backups, logs opt-in | `$XDG_STATE_HOME/omarchy-studio/` |
| Resultados descartáveis | `$XDG_CACHE_HOME/omarchy-studio/` |

Defaults são `~/.config`, `~/.local/share`, `~/.local/state` e `~/.cache`.
Overrides vazios ou relativos usam os defaults. O helper XDG já existe; o Doctor
não cria esses diretórios. A localização de instalação do plugin permanece
`~/.config/omarchy/plugins/<id>/`, literal do host 4.0.3, e não é relocada pelo helper.
