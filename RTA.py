import math

def RTA_test(Gamma):
    print(f"{'Task':<12} | {'C_i (us)':<10} | {'T_i (us)':<10} | {'B_i (us)':<10} | {'R_i (us)':<10} | {'Status':<8}")
    print("-" * 72)
    
    for i, tau_i in enumerate(Gamma):
        C_i = tau_i['C']
        T_i = tau_i['T']
        B_i = tau_i.get('B', 0)
        D_i = tau_i.get('D', T_i)
        
        R_i = C_i + B_i
        while True:
            R_old = R_i
            I_i = sum(
                math.ceil(R_old / Gamma[h]['T']) * Gamma[h]['C']
                for h in range(i)
            )
            R_i = C_i + B_i + I_i
            
            if R_i > D_i:
                print(f"{tau_i['name']:<12} | {C_i:<10} | {T_i:<10} | {B_i:<10} | {R_i:<10} | FAIL")
                return "UNSCHEDULABLE"
            if R_i <= R_old:
                print(f"{tau_i['name']:<12} | {C_i:<10} | {T_i:<10} | {B_i:<10} | {R_i:<10} | PASS")
                break

    return "SCHEDULABLE"

if __name__ == "__main__":
    node_tasks = [
        {'name': 'sampling',  'C': 18,   'T': 1000,   'B': 0},
        {'name': 'control',   'C': 3,    'T': 10000,  'B': 400}, # B_i from k_mutex
        {'name': 'display',   'C': 24733,'T': 500000, 'B': 0},
        {'name': 'telemetry', 'C': 6233, 'T': 1000000,'B': 0},
    ]
    
    verdict = RTA_test(node_tasks)
    print(f"\nFinal System Verdict: {verdict}")
