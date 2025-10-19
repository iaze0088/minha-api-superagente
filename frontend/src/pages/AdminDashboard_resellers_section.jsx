          {/* Resellers Tab - Gerenciamento Completo Multi-Tenant */}
          <TabsContent value="resellers" className="space-y-6">
            {/* Header com controles */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold">Gerenciar Revendas Multi-Tenant</h3>
                  <p className="text-sm text-slate-600 mt-1">Hierarquia completa com isolamento de dados</p>
                </div>
                <div className="flex gap-2">
                  <Button 
                    onClick={() => setViewMode(viewMode === 'list' ? 'tree' : 'list')} 
                    variant="outline"
                    size="sm"
                  >
                    <GitBranch className="w-4 h-4 mr-2" />
                    {viewMode === 'list' ? 'Ver Hierarquia' : 'Ver Lista'}
                  </Button>
                  <Button onClick={handleReplicateConfig} variant="outline" size="sm" className="bg-blue-600 text-white hover:bg-blue-700">
                    <Settings className="w-4 h-4 mr-2" />
                    Replicar Config
                  </Button>
                </div>
              </div>
              
              {/* Info Box */}
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4 mb-4">
                <p className="text-sm text-purple-900">
                  <strong>🌳 Sistema Multi-Tenant Hierárquico</strong><br />
                  • Cada revenda tem domínio próprio e dados isolados<br />
                  • Revendas podem criar sub-revendas (hierarquia ilimitada)<br />
                  • Transferência de revendas entre pais (Admin Master only)<br />
                  • Exclusão bloqueada se houver sub-revendas
                </p>
              </div>
              
              {/* Formulário de Criação */}
              <h4 className="font-semibold mb-3">Criar Nova Revenda</h4>
              <div className="grid md:grid-cols-3 gap-4 mb-4">
                <Input
                  placeholder="Nome da Revenda"
                  value={newReseller.name}
                  onChange={(e) => setNewReseller({ ...newReseller, name: e.target.value })}
                />
                <Input
                  placeholder="Email (login)"
                  type="email"
                  value={newReseller.email}
                  onChange={(e) => setNewReseller({ ...newReseller, email: e.target.value })}
                />
                <Input
                  type="password"
                  placeholder="Senha"
                  value={newReseller.password}
                  onChange={(e) => setNewReseller({ ...newReseller, password: e.target.value })}
                />
              </div>
              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <Input
                  placeholder="Domínio (opcional)"
                  value={newReseller.domain}
                  onChange={(e) => setNewReseller({ ...newReseller, domain: e.target.value })}
                />
                <Select value={newReseller.parent_id || 'root'} onValueChange={(val) => setNewReseller({ ...newReseller, parent_id: val === 'root' ? null : val })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Revenda Pai (Raiz se vazio)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="root">🌟 Revenda Raiz (Nível 0)</SelectItem>
                    {resellers.map(r => (
                      <SelectItem key={r.id} value={r.id}>
                        {'  '.repeat(r.level || 0)}└─ {r.name} (Nível {r.level || 0})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button onClick={handleCreateReseller} className="bg-purple-600 hover:bg-purple-700">
                <Plus className="w-4 h-4 mr-2" />
                Criar Revenda
              </Button>
            </Card>

            {/* Vista de Lista */}
            {viewMode === 'list' && (
              <div className="grid gap-4">
                {resellers.length === 0 ? (
                  <Card className="p-8 text-center">
                    <Users className="w-16 h-16 mx-auto text-slate-300 mb-4" />
                    <p className="text-slate-600">Nenhuma revenda criada ainda</p>
                    <p className="text-sm text-slate-500 mt-2">Crie sua primeira revenda acima</p>
                  </Card>
                ) : (
                  resellers.map((reseller) => (
                    <Card key={reseller.id} className="p-6 hover:shadow-lg transition-shadow">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          {/* Header com Nível */}
                          <div className="flex items-center gap-3 mb-2">
                            <span className="text-2xl">{reseller.level === 0 ? '🌟' : reseller.level === 1 ? '📦' : '📁'}</span>
                            <div>
                              <h4 className="font-semibold text-slate-900 text-lg">{reseller.name}</h4>
                              <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                                Nível {reseller.level || 0} {reseller.parent_id ? '(Sub-revenda)' : '(Raiz)'}
                              </span>
                            </div>
                          </div>
                          
                          {/* Informações */}
                          <div className="space-y-1 text-sm text-slate-600">
                            <p>✉️ Email: {reseller.email}</p>
                            {reseller.domain && <p>🔗 Subdomínio: {reseller.domain}</p>}
                            {reseller.custom_domain && (
                              <p className="text-emerald-600 font-medium">✅ Domínio: {reseller.custom_domain}</p>
                            )}
                            {reseller.children_count > 0 && (
                              <p className="text-orange-600 font-medium">
                                👥 {reseller.children_count} Sub-revenda(s)
                              </p>
                            )}
                            <p className="text-xs text-slate-500">
                              📅 Criado: {new Date(reseller.created_at).toLocaleDateString('pt-BR')}
                            </p>
                          </div>

                          {/* Domínio Customizado */}
                          <div className="mt-3 flex gap-2">
                            <Input
                              placeholder="Domínio customizado (ex: ajuda.vip)"
                              defaultValue={reseller.custom_domain}
                              id={`domain-${reseller.id}`}
                              className="text-sm flex-1"
                            />
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={async () => {
                                const input = document.getElementById(`domain-${reseller.id}`);
                                const domain = input.value.trim();
                                try {
                                  await api.put(`/resellers/${reseller.id}`, { custom_domain: domain });
                                  toast.success('Domínio atualizado!');
                                  loadData();
                                } catch (error) {
                                  toast.error('Erro ao atualizar domínio');
                                }
                              }}
                            >
                              💾 Salvar
                            </Button>
                          </div>

                          {/* Status */}
                          <div className="mt-3">
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                              reseller.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                            }`}>
                              {reseller.is_active ? '✓ Ativa' : '✗ Inativa'}
                            </span>
                          </div>
                        </div>

                        {/* Ações */}
                        <div className="flex flex-col gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => window.open(`/revenda/login?email=${reseller.email}`, '_blank')}
                          >
                            🚀 Ver Painel
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setTransferModal({ open: true, reseller, new_parent_id: null })}
                          >
                            <ArrowRightLeft className="w-4 h-4 mr-1" />
                            Transferir
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDeleteReseller(reseller.id)}
                            className="text-red-600 hover:bg-red-50"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </Card>
                  ))
                )}
              </div>
            )}

            {/* Vista de Árvore Hierárquica */}
            {viewMode === 'tree' && (
              <Card className="p-6">
                <h4 className="font-semibold mb-4 flex items-center gap-2">
                  <GitBranch className="w-5 h-5" />
                  Hierarquia de Revendas
                </h4>
                
                {hierarchy.hierarchy && hierarchy.hierarchy.length > 0 ? (
                  <div className="space-y-2">
                    {hierarchy.hierarchy.map(reseller => (
                      <ResellerTreeNode 
                        key={reseller.id} 
                        reseller={reseller} 
                        level={0}
                        expandedResellers={expandedResellers}
                        toggleExpand={toggleExpand}
                        handleDeleteReseller={handleDeleteReseller}
                        setTransferModal={setTransferModal}
                      />
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 text-center py-8">Nenhuma revenda na hierarquia</p>
                )}
              </Card>
            )}
          </TabsContent>

          {/* Modal de Transferência */}
          <Dialog open={transferModal.open} onOpenChange={(open) => setTransferModal({ ...transferModal, open })}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Transferir Revenda</DialogTitle>
              </DialogHeader>
              {transferModal.reseller && (
                <div className="space-y-4">
                  <div className="bg-slate-50 p-4 rounded">
                    <p className="text-sm text-slate-600">Revenda:</p>
                    <p className="font-semibold">{transferModal.reseller.name}</p>
                    <p className="text-xs text-slate-500">Nível atual: {transferModal.reseller.level || 0}</p>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium mb-2 block">Nova Revenda Pai:</label>
                    <Select 
                      value={transferModal.new_parent_id || 'root'} 
                      onValueChange={(val) => setTransferModal({ ...transferModal, new_parent_id: val === 'root' ? null : val })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecionar nova pai" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="root">🌟 Tornar Raiz (Nível 0)</SelectItem>
                        {resellers
                          .filter(r => r.id !== transferModal.reseller.id)
                          .map(r => (
                            <SelectItem key={r.id} value={r.id}>
                              {'  '.repeat(r.level || 0)}└─ {r.name} (Nível {r.level || 0})
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex gap-2 justify-end">
                    <Button variant="outline" onClick={() => setTransferModal({ open: false, reseller: null })}>
                      Cancelar
                    </Button>
                    <Button onClick={handleTransferReseller} className="bg-purple-600 hover:bg-purple-700">
                      Transferir
                    </Button>
                  </div>
                </div>
              )}
            </DialogContent>
          </Dialog>
