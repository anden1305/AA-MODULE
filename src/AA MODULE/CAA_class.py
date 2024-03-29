########## IMPORTS ##########
import torch
import torch.nn as nn
import torch.optim as optim
from timeit import default_timer as timer 
from loading_bar_class import _loading_bar
from AA_result_class import _CAA_result


########## CONVENTIONAL ARCHETYPAL ANALYSIS CLASS ##########
class _CAA:

    ########## HELPER FUNCTION // EARLY STOPPING ##########
    def _early_stopping(self):
        next_imp = self.RSS[-round(len(self.RSS)/100)]-self.RSS[-1]
        prev_imp = (self.RSS[0]-self.RSS[-1])*1e-5
        return next_imp < prev_imp

    ########## HELPER FUNCTION // CALCULATE ERROR FOR EACH ITERATION ##########
    def _error(self, X,B,A):
        return torch.norm(X - X@B@A, p='fro')**2
    
    ########## HELPER FUNCTION // A CONSTRAINTS ##########
    def _apply_constraints(self, A):
        m = nn.Softmax(dim=0)
        return m(A)
    
    ########## COMPUTE ARCHETYPES FUNCTION OF CAA ##########
    def _compute_archetypes(self, X, K, p, n_iter, lr, mute,columns,with_synthetic_data = False, early_stopping = False, for_hotstart_usage = False):

        ########## INITIALIZATION ##########
        self.RSS = []
        start = timer()
        if not mute:
            loading_bar = _loading_bar(n_iter, "Conventional Arhcetypal Analysis")
        N, _ = X.T.shape
        Xt = torch.tensor(X,requires_grad=False).float()
        A = torch.autograd.Variable(torch.rand(K, N), requires_grad=True)
        B = torch.autograd.Variable(torch.rand(N, K), requires_grad=True)
        optimizer = optim.Adam([A, B], amsgrad = True, lr = lr)
        


        ########## ANALYSIS ##########
        for i in range(n_iter):
            if not mute:
                loading_bar._update()
            optimizer.zero_grad()
            L = self._error(Xt, self._apply_constraints(B), self._apply_constraints(A))
            self.RSS.append(L.detach().numpy())
            L.backward()
            optimizer.step()

            ########## EARLY STOPPING ##########
            if i % 25 == 0 and early_stopping:
                if len(self.RSS) > 200 and self._early_stopping():
                    if not mute:
                        loading_bar._kill()
                        print("Analysis ended due to early stopping.\n")
                    break
        
        

        ########## POST ANALYSIS ##########
        A_f = self._apply_constraints(A).detach().numpy()
        B_f = self._apply_constraints(B).detach().numpy()
        Z_f = (Xt@self._apply_constraints(B)).detach().numpy()
        X_hat_f = X@B_f@A_f
        end = timer()
        time = round(end-start,2)
        result = _CAA_result(A_f, B_f, X, X_hat_f, n_iter, self.RSS, Z_f, K, p, time,columns,"CAA",with_synthetic_data = with_synthetic_data)

        if not mute:
            result._print()

        if not for_hotstart_usage:
            return result
        else:
            return A.detach().numpy(), B.detach().numpy()