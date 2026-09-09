# Hardware / sessão gráfica — protocolo manual

Nenhum teste aqui roda automaticamente. Usar usuário de teste em Omarchy 4.0.3,
registrar commit Studio, versão/arquitetura Omarchy, kernel, PipeWire,
WirePlumber, interface exata, firmware conhecido e tipo de conexão. Se desconhecido,
registrar UNKNOWN. Não publicar seriais ou dados de projetos pessoais.

1. Validar o manifesto. Instalar o repositório commitado com o comando oficial.
   Verificar a entrada Studio nas barras horizontal e vertical e em dois monitores.
2. Clicar em Studio: um terminal apresenta o relatório e aguarda Enter. Verificar
   caminho com espaços, terminal padrão e erro visível se o launcher falhar.
   Não deve existir polling de diagnóstico ou daemon Studio em idle.
3. Comparar o relatório com as fontes locais: pacman, serviços de usuário, dump
   PipeWire, placas procfs/sysfs e políticas por thread. Gravar JSON revisado.
4. Repetir sem interface, com uma e com múltiplas interfaces. Confirmar identidade,
   hotplug e índices novos sem duplicações/associações falsas. Não chamar contagem
   de PCMs de contagem de canais.
5. Repetir com MIDI físico e software. Conferir clientes/portas/direções; System
   Timer não pode ser apresentado como controlador musical.
6. Com uma sessão DAW legítima já preparada pelo operador, observar captura e
   reprodução e comparar hw_params ativos. Conferir estados idle/suspended.
   Não alterar quantum, volume, limites ou plugins por ação do Doctor.
7. Repetir o Doctor duas vezes. Conferir ausência de escrita em configurações e
   dependências. Salvar evidência somente por exportação explícita.
8. Desabilitar/reabilitar; testar atualização por fast-forward e rollback manual
   em cópia de teste. Remover usando o gerenciador. Conferir continuidade do áudio,
   ausência de alterações em arquivos de áudio e entrada de barra removida.

Medir gravação, emissão de sinal, XRUNs, latência de ida e volta, drift e estabilidade
de carga é um procedimento futuro separado, com consentimento explícito para
emitir/capturar áudio e nível de monitoramento definido pelo operador. Nenhum score
de 0.1 aprova automaticamente esses testes.

Modelo de registro:

```text
Date / operator / Studio commit:
Omarchy / kernel / architecture:
PipeWire / WirePlumber:
Device model / revision / firmware / transport:
DAW / workload (if used):
Steps completed and evidence:
Observed results:
Unknowns / limitations:
Support classification and source (default UNKNOWN):
```
