import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ServicesPage } from './services';
import { SERVICE } from '../../../testing/fixtures';

describe('Gerenciamento de serviços', () => {
  let http: HttpTestingController;
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());
  function loaded(items = [SERVICE]) {
    const fixture = TestBed.createComponent(ServicesPage);
    http.expectOne((r) => r.url === '/api/admin/servicos').flush(items);
    fixture.detectChanges();
    return fixture;
  }
  function reload(items = [SERVICE]) {
    http.expectOne((r) => r.url === '/api/admin/servicos').flush(items);
  }
  function fill(page: ServicesPage) {
    page.form.setValue({
      nome: 'Tranças',
      descricao: '',
      preco: '0,50',
      duracao_minutos: 60,
      ativo: true,
    });
  }
  function choose(page: ServicesPage, file: File | null) {
    const input = document.createElement('input');
    input.type = 'file';
    Object.defineProperty(input, 'files', { value: file ? [file] : null });
    page.selectFile({ target: input } as unknown as Event);
  }
  it('impede edição e nova mutação enquanto a reativação atualiza a lista', () => {
    const fixture = loaded([
        { ...SERVICE, ativo: false },
        { ...SERVICE, id: 'outro' },
      ]),
      page = fixture.componentInstance;
    page.toggle({ ...SERVICE, ativo: false });
    http.expectOne(`/api/admin/servicos/${SERVICE.id}`).flush(SERVICE);
    expect(page.services()[0].ativo).toBe(true);
    expect(page.services()[1].id).toBe('outro');
    expect(page.loading()).toBe(true);
    page.edit({ ...SERVICE, ativo: false });
    page.toggle(SERVICE);
    page.save();
    expect(page.opened()).toBe(false);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('button').disabled).toBe(true);
    reload();
    page.edit(SERVICE);
    expect(page.form.controls.ativo.value).toBe(true);
  });
  it('mostra estado vazio e valida formulário sem enviar dados inválidos', () => {
    const fixture = loaded([]),
      page = fixture.componentInstance;
    expect(fixture.nativeElement.textContent).toContain('Nenhum serviço cadastrado');
    page.edit(null);
    page.save();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Informe um preço positivo');
    http.expectNone('/api/admin/servicos');
  });
  it('cadastra, normaliza preço com vírgula e descrição vazia, evitando duplicação', () => {
    const fixture = loaded(),
      page = fixture.componentInstance;
    page.edit(null);
    fill(page);
    page.save();
    page.save();
    const req = http.expectOne('/api/admin/servicos');
    expect(req.request.body.preco).toBe('0.50');
    expect(req.request.body.descricao).toBeNull();
    req.flush(SERVICE);
    reload();
    fixture.detectChanges();
    expect(page.opened()).toBe(false);
    expect(page.success()).toContain('salvo');
  });
  it('edita campos e preserva identidade, enviando descrição preenchida', () => {
    const fixture = loaded(),
      page = fixture.componentInstance;
    page.edit({ ...SERVICE, descricao: null });
    expect(page.form.controls.descricao.value).toBe('');
    page.form.controls.descricao.setValue('Descrição');
    page.save();
    const req = http.expectOne(`/api/admin/servicos/${SERVICE.id}`);
    expect(req.request.method).toBe('PUT');
    expect(req.request.body.descricao).toBe('Descrição');
    req.flush(SERVICE);
    reload();
  });
  it.each(['image/jpeg', 'image/png', 'image/webp'])(
    'permite foto %s e envia depois da persistência do serviço',
    (type) => {
      const fixture = loaded(),
        page = fixture.componentInstance;
      page.edit(null);
      fill(page);
      const file = new File(['foto'], 'foto', { type });
      choose(page, file);
      page.save();
      http.expectOne('/api/admin/servicos').flush(SERVICE);
      const upload = http.expectOne(`/api/admin/servicos/${SERVICE.id}/foto`);
      expect(upload.request.body).toBe(file);
      upload.flush({ ...SERVICE, imagem_url: '/foto' });
      reload();
      expect(page.file()).toBeNull();
    },
  );
  it('valida tipo/tamanho e trata cancelamento da escolha de foto', () => {
    const fixture = loaded(),
      page = fixture.componentInstance;
    page.edit(null);
    fill(page);
    choose(page, new File(['exe'], 'a.exe', { type: 'application/octet-stream' }));
    expect(page.fileError()).toContain('JPEG');
    page.save();
    http.expectNone('/api/admin/servicos');
    choose(page, new File([new Uint8Array(5 * 1024 * 1024 + 1)], 'a.png', { type: 'image/png' }));
    expect(page.fileError()).toContain('5 MB');
    choose(page, null);
    expect(page.fileError()).toBe('');
    expect(page.file()).toBeNull();
  });
  it('falha ao cadastrar mantém formulário e não declara sucesso', () => {
    const fixture = loaded(),
      page = fixture.componentInstance;
    page.edit(null);
    fill(page);
    page.save();
    http.expectOne('/api/admin/servicos').flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();
    expect(page.busy()).toBe(false);
    expect(page.opened()).toBe(true);
    expect(page.success()).toBe('');
    expect(fixture.nativeElement.querySelector('[role=alert]')).not.toBeNull();
  });
  it('falha na foto preserva ID salvo para não criar serviço duplicado na nova tentativa', () => {
    const fixture = loaded(),
      page = fixture.componentInstance;
    page.edit(null);
    fill(page);
    choose(page, new File(['foto'], 'a.png', { type: 'image/png' }));
    page.save();
    http.expectOne('/api/admin/servicos').flush(SERVICE);
    http
      .expectOne(`/api/admin/servicos/${SERVICE.id}/foto`)
      .flush({}, { status: 503, statusText: 'Unavailable' });
    expect(page.error()).toContain('serviço foi salvo');
    expect(page.editing()?.id).toBe(SERVICE.id);
    page.save();
    const retry = http.expectOne(`/api/admin/servicos/${SERVICE.id}`);
    expect(retry.request.method).toBe('PUT');
    retry.flush(SERVICE);
    http.expectOne(`/api/admin/servicos/${SERVICE.id}/foto`).flush(SERVICE);
    reload();
  });
  it.each([true, false])('altera ativo=%s sem excluir histórico', (ativo) => {
    const fixture = loaded(),
      page = fixture.componentInstance;
    page.toggle({ ...SERVICE, ativo });
    page.toggle(SERVICE);
    const req = http.expectOne(`/api/admin/servicos/${SERVICE.id}`);
    expect(req.request.body.ativo).toBe(!ativo);
    req.flush({ ...SERVICE, ativo: !ativo });
    reload();
    expect(page.success()).toContain(ativo ? 'desativado' : 'reativado');
  });
  it('trata erro ao ativar/desativar e mantém estado existente', () => {
    const fixture = loaded(),
      page = fixture.componentInstance;
    page.toggle(SERVICE);
    http
      .expectOne(`/api/admin/servicos/${SERVICE.id}`)
      .flush({}, { status: 409, statusText: 'Conflict' });
    expect(page.busy()).toBe(false);
    expect(page.services()[0].ativo).toBe(true);
    expect(page.error()).toContain('alterados');
  });
  it('remove foto apenas de serviço salvo e trata concorrência de botões', () => {
    const fixture = loaded(),
      page = fixture.componentInstance;
    page.removePhoto();
    http.expectNone(() => true);
    page.edit({ ...SERVICE, imagem_url: '/foto' });
    page.removePhoto();
    page.removePhoto();
    http.expectOne(`/api/admin/servicos/${SERVICE.id}/foto`).flush(SERVICE);
    reload();
    expect(page.success()).toBe('Foto removida.');
    expect(page.editing()?.imagem_url).toBeNull();
  });
  it('trata erro ao remover foto sem apagar referência local', () => {
    const fixture = loaded(),
      page = fixture.componentInstance;
    page.edit({ ...SERVICE, imagem_url: '/foto' });
    page.removePhoto();
    http
      .expectOne(`/api/admin/servicos/${SERVICE.id}/foto`)
      .flush({}, { status: 503, statusText: 'Unavailable' });
    expect(page.editing()?.imagem_url).toBe('/foto');
    expect(page.busy()).toBe(false);
    expect(page.error()).not.toBe('');
  });
  it('carregamento com falha permite tentar novamente', () => {
    const fixture = TestBed.createComponent(ServicesPage);
    http.expectOne((r) => r.url === '/api/admin/servicos').error(new ProgressEvent('error'));
    fixture.detectChanges();
    expect(fixture.componentInstance.loading()).toBe(false);
    fixture.componentInstance.load();
    reload();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Box Braids');
  });
});
