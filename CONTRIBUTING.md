# Contribuir

A primeira entrega é o Doctor sem mutações. Consulte a pesquisa do Omarchy antes
de propor integração; não adicione campos imaginários ao manifesto ou modifique
arquivos do Omarchy para instalar funcionalidades do Studio.

Mantenha chamadas externas em Host/probes, política de score em readiness e
apresentação em CLI/QML. Use biblioteca padrão sempre que suficiente. Uma nova
dependência precisa justificar empacotamento, manutenção e superfície de execução.
Suporte a fabricante/modelo precisa de evidência e escopo de versão.

Execute as suítes unitária e de integração descritas em `docs/testing.md`. Para
mudanças no QML, inclua teste em sessão Omarchy e descreva o que não foi validado.
PRs devem informar problema, comportamento final, evidência dos testes e limites.
Não inclua logs pessoais, seriais, instaladores comerciais ou credenciais.

O projeto usa MIT. Ajustes incompatíveis no relatório ou nas métricas exigem
versionamento explícito e atualização dos documentos. Uma release precisa manter
manifest.json, pyproject.toml e `__version__` consistentes, com revisão de contrato
do Omarchy e registro dos gates de hardware pendentes/aprovados.
