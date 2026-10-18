import { TestBed } from '@angular/core/testing';
import { Feedback } from './feedback';

describe('Avisos de resultado', () => {
  it('mostra confirmação acessível, permite fechar e reaparece para uma nova mensagem', () => {
    const fixture = TestBed.createComponent(Feedback);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.feedback-panel')).toBeNull();
    fixture.componentRef.setInput('success', 'Horário disponibilizado.');
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role=status]').textContent).toContain(
      'Horário disponibilizado.',
    );
    expect(fixture.nativeElement.querySelector('[aria-atomic=true]')).not.toBeNull();
    fixture.nativeElement.querySelector('button').click();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.feedback-panel')).toBeNull();
    fixture.componentRef.setInput('success', 'Serviço salvo com sucesso.');
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role=status]').textContent).toContain(
      'Serviço salvo',
    );
  });

  it('prioriza o erro sobre sucesso anterior, sem interpretar HTML recebido', () => {
    const fixture = TestBed.createComponent(Feedback);
    fixture.componentRef.setInput('success', 'Salvo anteriormente.');
    fixture.componentRef.setInput('error', '<img src=x onerror=alert(1)> Não foi possível salvar.');
    fixture.detectChanges();
    const panel = fixture.nativeElement.querySelector('[role=alert]');
    expect(panel.textContent).toContain('Não foi possível salvar.');
    expect(panel.textContent).not.toContain('Salvo anteriormente.');
    expect(panel.querySelector('img')).toBeNull();
    expect(panel.querySelector('button').getAttribute('aria-label')).toBe('Fechar aviso');
  });
});
