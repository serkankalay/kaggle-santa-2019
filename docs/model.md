---
marp: true
theme: gaia
_class: lead
backgroundColor: #fff
---


# **Santa 2019**

### MIP

---
## Assumptions

- All the families can be assigned to one of their choices.

---
## Indices

- $d$: days
- $f$: families
- $o$: occupancy level, $MIN_O \le o \le MAX_O$

---
## Sets

- $D$: days
- $F$: families
- $D(f)$: choices of family $f$
- $O$: [$MIN_O$, $MAX_O$]

---
## Parameters

- $MIN_O$: Minimum daily occupancy (125)
- $MAX_O$: Maximum daily occupancy (300)
- $c_{fd}$: Cost of assigning family $f$ to $d$
- $n_f$: Number of members of $f$
- $c_{oo'}$: Cost of having $o$ and $o'$ in consecutive days


---
## Variables

- $X_{fd}$: If family $f$ is assigned to $d$
- $\delta_{od}$: If family $o$ is the occupancy level in $d$
- $\phi_{oo'd}$: If occupancy is $o$ for $d$ and $o'$ for $d+1$
<!-- - $Z_{f}$: If family $f$ is not assigned, _i.e._ assigned to none of the choices -->
<!-- - $\phi_{d}$: If $n$ overflow/extra starting capacity is available on $d$
- $\gamma_{nd}$: If $n$ overflow/extra FTE is available on $d$
- $\delta_{cd}$: If crew $c$ is _conflicted_ on $d$ -->


---
## Constraints

- Assignment constraints 
<!-- $\sum_{d \in D(f)} X_{fd} + Z_f = 1 \quad \forall c \in C$ -->
$\sum_{d \in D(f)} X_{fd} = 1 \quad \forall c \in C$

- Occupancy consistency
$\sum_{MIN_O \le o \le MAX_O} \delta_{od} = 1 \quad \forall d \in D$


---
## Constraints (contd.)

- Occupancy levels
$\sum_{f \in F} X_{fd} * n_f = \sum_{o \in O} o * \delta_{od} \quad \forall d \in D$

---
## Constraints - Occupancy Pairs v1

- Occupancy pairs (non-linear)
$\delta_{od} * \delta_{o'd+1} \le \phi_{oo'd} \quad \forall d \in D, o \in O$

- Occupancy pairs (linearized)
$\phi_{oo'd} \le \delta_{od} \quad \forall d \in D, o \in O$
$\phi_{oo'd} \le \delta_{o'd+1} \quad \forall d+1 \in D, o \in O$
$\phi_{oo'd} \ge \delta_{od} + \delta_{o'd+1} - 1 \quad \forall d \in D, o \in O$ 

$\phi$ can be relaxed

---
## Constraints - Occupancy Pairs v2

- Occupancy pairs
$\sum_{o' \in O} \phi_{oo'd} = \delta_{od} \quad \forall o \in O, d \in D$
$\sum_{o \in O} \phi_{oo'd} = \delta_{o'd+1} \quad \forall o' \in O, d \in D$

$\phi$ needs to be defined as binary


---
## Objective

- Minimize costs 

$Min \quad \sum_{f \in F}\sum_{d \in D(f)} c_{fd} * X_{fd} + \sum_{(o, o') \in O}\sum_{d \in D} c_{oo'} \phi_{oo'd}$