"""Correct the two diagnosed mirrored-basis helpers in the frozen generator."""

REPLACEMENTS = [(' poly(v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],ma)', ' f=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]\n if t[0]*n[1]-t[1]*n[0]<0:f=[tuple(reversed(face)) for face in f]\n poly(v,f,ma)'), ('  poly(vs,[(k,(k+1)%16,(k+1)%16+16,k+16) for k in range(16)],1)', '  f=[(k,(k+1)%16,(k+1)%16+16,k+16) for k in range(16)]\n  if t[0]*n[1]-t[1]*n[0]<0:f=[tuple(reversed(face)) for face in f]\n  poly(vs,f,1)')]

def corrected_source(source):
    for before, after in REPLACEMENTS:
        if source.count(before) != 1:
            raise ValueError("Generator differs from diagnosed baseline; refusing an unverified repair")
        source = source.replace(before, after, 1)
    return source
