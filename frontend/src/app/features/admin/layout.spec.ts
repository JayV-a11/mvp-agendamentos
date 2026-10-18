import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { SessionStore } from '../../core/session-store';
import { SESSION } from '../../../testing/fixtures';
import { AdminLayout } from './layout';
import { Activity } from '../../core/activity';

describe('Navegação administrativa', () => {
  let http: HttpTestingController;
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());
  it('revoga sessão e volta ao login, impedindo clique duplicado', async () => {
    const navigate = vi.spyOn(TestBed.inject(Router), 'navigateByUrl').mockResolvedValue(true);
    TestBed.inject(SessionStore).session.set(SESSION);
    const fixture = TestBed.createComponent(AdminLayout);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('nav').getAttribute('aria-label')).toBe(
      'Administração',
    );
    fixture.nativeElement.querySelector('button').click();
    fixture.componentInstance.logout();
    http.expectOne('/api/auth/logout').flush(null);
    expect(TestBed.inject(SessionStore).session()).toBeNull();
    expect(navigate).toHaveBeenCalledWith('/login');
    await Promise.resolve();
    expect(TestBed.inject(Activity).sessionSuccess()).toContain('saiu da sua conta com segurança');
  });
  it('não apresenta logout como concluído quando a API falha', () => {
    const fixture = TestBed.createComponent(AdminLayout);
    fixture.componentInstance.logout();
    http.expectOne('/api/auth/logout').flush({}, { status: 503, statusText: 'Unavailable' });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role=alert]')).not.toBeNull();
    expect(fixture.componentInstance.busy()).toBe(false);
    fixture.nativeElement.querySelector('.feedback-close').click();
    fixture.detectChanges();
    expect(fixture.componentInstance.error()).toBe('');
    expect(fixture.nativeElement.querySelector('[role=alert]')).toBeNull();
  });
});
