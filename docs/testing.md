# Estratégia de testes

## Unitários

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests/unit -v
```

Fixtures sintéticas substituem sistema de arquivos, pacotes, serviços, grafo e
threads. Cobrem PipeWire saudável/ausente, WirePlumber ausente, JACK opcional,
rtkit ausente, RT presente/ausente/desconhecido, nenhuma/uma/múltiplas placas,
hardware desconhecido/virtual, MIDI, saídas inesperadas, falhas e versões Omarchy
incompatíveis. Testes do executor usam processos Python descartáveis para timeout,
limite de saída, descendentes, ausência de comandos e argumentos literais.

## Integração

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  OMARCHY_UPSTREAM=/caminho/para/omarchy-4.0.3 \
  python3 -m unittest discover -s tests/integration -v
```

Testa executável real, JSON, stderr verbose, exit codes, ausência de escrita no
HOME temporário, caminhos com espaços/metacaracteres, wrapper de terminal e
manifesto com o validador **do upstream**, sem cópia divergente da especificação.
O teste do validador é skipped se OMARCHY_UPSTREAM não for definido. O ambiente
temporário não é um estúdio: não se instalam nem emulam daemons PipeWire em CI.

GitHub Actions testa Python 3.11–3.14, com permissões somente de leitura, ações
fixadas por SHA e validador na revisão `0534987009061cbe2dacdde4ad564092ab698d12`.
Um workflow definido localmente ainda não é execução remota de CI.

Opcionalmente valide os relatórios com uma implementação JSON Schema draft
2020-12. O projeto fornece o contrato, e seus testes de comportamento também
verificam soma, denominador, estados e distinção entre null/false.

## Sessão Omarchy e hardware

O protocolo de [hardware](../tests/hardware/README.md) é separado e manual.
Validar manifesto não carrega QML. Validar QML, por sua vez, não comprova áudio,
hotplug ou latência. Não marcar um gate como aprovado por inferência.

| Gate | Ambiente desta implementação |
|---|---|
| Python e fixtures | executável em Ubuntu/WSL2, Python 3.14 |
| CLI e validador oficial 4.0.3 | executável localmente |
| QML em Omarchy 4.0.3/Hyprland | pendente; Quickshell indisponível aqui |
| Instalar/habilitar/atualizar/remover na sessão | pendente em usuário Omarchy de teste |
| Interface, MIDI, gravação e latência | pendente em hardware real |

Registro local em 2026-09-09: 63 testes passaram em Python 3.14.4, incluindo o
validador oficial 4.0.3. Também foram verificados sintaxe Bash/Python, ausência de
symlinks e links locais da documentação. O schema draft 2020-12 e três relatórios
(fixture completa, fixture vazia e sistema local) foram validados com jsonschema
4.19.2 disponível no ambiente. Nenhum resultado de CI remoto é reivindicado.

Qualquer release apresentada como validada para músicos deverá anexar evidências
dos gates de sessão/hardware, sem transformar testes sintéticos em matriz de
compatibilidade. Novos coletores devem adicionar fixtures de origem conhecida e
testes para indisponibilidade, mudanças de schema e acesso insuficiente.
