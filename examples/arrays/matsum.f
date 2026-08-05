      PROGRAM MATSUM
      IMPLICIT NONE
      INTEGER A(3,2)
      INTEGER I, J, TOTAL

      A(1,1) = 1
      A(2,1) = 2
      A(3,1) = 3
      A(1,2) = 4
      A(2,2) = 5
      A(3,2) = 6

*     Menjumlahkan setiap elemen
      TOTAL = 0
      DO 10 I = 1, 3
          DO 10 J = 1, 2
              TOTAL = TOTAL + A(I,J)
   10 CONTINUE

      PRINT *, TOTAL
      END