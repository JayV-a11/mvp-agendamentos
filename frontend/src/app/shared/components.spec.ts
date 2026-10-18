import { TestBed } from '@angular/core/testing';
import { FormControl, Validators } from '@angular/forms';
import { FieldError, Heading, ServiceImage, StatusBadge } from './components';
import { SERVICE } from '../../testing/fixtures';

describe('Componentes compartilhados', () => {
  it('apresenta identidade e subtítulo com texto sem HTML dinâmico', () => {
    const fixture = TestBed.createComponent(Heading);
    fixture.componentRef.setInput('subtitle', '<script>texto</script>');
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Tranças & Estilo');
    expect(fixture.nativeElement.querySelector('script')).toBeNull();
  });
  it('apresenta erro apenas após interação com campo inválido', () => {
    const fixture = TestBed.createComponent(FieldError);
    const control = new FormControl('', Validators.required);
    fixture.componentRef.setInput('control', control);
    fixture.componentRef.setInput('message', 'Campo obrigatório');
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent.trim()).toBe('');
    control.markAsTouched();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Campo obrigatório');
    control.setValue('Válido');
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent.trim()).toBe('');
  });
  it.each([
    ['pendente', 'Pendente'],
    ['aprovado', 'Aprovado'],
    ['recusado', 'Recusado'],
    ['cancelado', 'Cancelado'],
  ])('descreve estado %s sem depender apenas de cor', (status, label) => {
    const fixture = TestBed.createComponent(StatusBadge);
    fixture.componentRef.setInput('status', status);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain(label);
  });
  it('usa placeholder acessível e fallback quando a imagem falha', () => {
    const fixture = TestBed.createComponent(ServiceImage);
    fixture.componentRef.setInput('service', SERVICE);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role=img]').getAttribute('aria-label')).toContain(
      'sem fotografia',
    );
    fixture.componentRef.setInput('service', {
      ...SERVICE,
      imagem_url: `/publico/servicos/${SERVICE.id}/foto?versao=uuid`,
    });
    fixture.detectChanges();
    const img = fixture.nativeElement.querySelector('img');
    expect(img.src).toContain('/api/publico/servicos/service-1/foto?versao=uuid');
    expect(img.alt).toContain('Box Braids');
    img.dispatchEvent(new Event('error'));
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('img')).toBeNull();
  });
  it('obtém foto inativa pelo endpoint administrativo e aceita referência sem query', () => {
    const fixture = TestBed.createComponent(ServiceImage);
    fixture.componentRef.setInput('service', { ...SERVICE, imagem_url: '/foto' });
    fixture.componentRef.setInput('admin', true);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('img').src).toContain(
      '/api/admin/servicos/service-1/foto?',
    );
  });
});
