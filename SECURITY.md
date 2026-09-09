# Segurança e privacidade

Studio 0.1 executa como usuário, sem sudo, mudanças em sudoers/limits, abertura
de dispositivos para gravação, downloads, instalação de pacotes ou telemetria.
Processos usam argv separado, stdin fechado, timeout e limite de saída. Não existe
shell=True, execução de conteúdo de metadados ou interpretação de labels como
comandos. Arquivos de configuração são inventariados sem ler seu conteúdo.

O widget é código QML executado dentro do shell Omarchy; as fachadas do host não
equivalem a sandbox. Leia o código e as atualizações antes de habilitar qualquer
plugin. O ciclo oficial de instalação mantém suas próprias confirmações.

O relatório seleciona campos conhecidos e não inclui serial USB, dump integral
de clientes, inventário de todos os pacotes ou logs de sessão. Nomes de portas,
dispositivos e caminhos de erro verbose ainda podem conter dados pessoais. Revise
arquivos exportados antes de compartilhá-los. Não há envio automático.

Configuração de runtime PATH e binários locais confiáveis pertence ao ambiente
do usuário. O Doctor não verifica integridade de todo o sistema nem torna segura
uma sessão já comprometida. Adaptadores privilegiados futuros precisam de modelo
de ameaça, allowlist de operações e testes de restauração antes de serem incluídos.

Para relatar uma vulnerabilidade, use um canal privado do mantenedor ou o recurso
de private vulnerability reporting do repositório, quando habilitado. O projeto
ainda não publicou um endereço dedicado nem uma promessa de SLA. Não anexe
credenciais, relatórios pessoais completos ou dados de outros usuários em issues
públicas. Bugs comuns podem ser relatados com versões e fixture sanitizada mínima.
