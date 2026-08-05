      PROGRAM LEXDEMO
      IMPLICIT NONE
      INTEGER I, N
      REAL X, Y, RESULT
      LOGICAL FLAG

      N = 10
      X = 3.14
      Y = .5E2
      FLAG = .TRUE.

      IF (N .GT. 0 .AND. FLAG) THEN
          RESULT = X * Y + N / 2.0 - X ** 2
      ELSE
          RESULT = 0.0
      ENDIF

   10 CONTINUE
      CALL SHOW(RESULT)

      END

      SUBROUTINE SHOW(VAL)
      IMPLICIT NONE
      REAL VAL
      PRINT *, VAL
      RETURN
      END