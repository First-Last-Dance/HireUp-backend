export class CodedError extends Error {
  code: number;

  constructor(message: string, code: number) {
    super(message);
    this.code = code;
  }
}
// message enum
export enum ErrorMessage {
  AccountNotFound = 'Account not found',
  JobNotFound = 'Job not found',
  UserAlreadyExist = 'User already exist',
  EmailAlreadyExist = 'Email already exist',
  PhoneNumberAlreadyExist = 'phone number already exist',
  NationalIDAlreadyExist = ' National ID already exist',
  InvalidBirthDate = 'Invalid birthDate',
  InvalidGender = 'Invalid gender',
  InvalidRole = 'Invalid role',
  InvalidEmail = 'Invalid Email',
  WrongPassword = 'Wrong password',
  UserAlreadyAuthorized = 'User already authorized',
  UserNotAuthorized = 'User not authorized',
  StadiumNotFound = 'Stadium not found',
  StadiumAlreadyExist = 'Stadium already exist',
  InvalidNumberOfRows = 'Number of rows must be greater than zero',
  InvalidNumberOfSeatsPerRow = 'Number of seats per row must be greater than zero',
  MatchNotFound = 'Match not found',
  InvalidTeamCompensations = 'Both teams can not be the same',
  InvalidDate = 'Invalid date',
  HomeTeamBusy = 'Home team is busy that day',
  AwayTeamBusy = 'Away team is busy that day',
  matchVenueBusy = 'Match venue is busy that day',
  mainRefereeBusy = 'Main referee is busy that day',
  firstLinesmanBusy = 'First Linesman is busy that day',
  secondLinesmanBusy = 'Second Linesman is busy that day',
  CanNotCancel = 'can not cancel reservation',
  InternalServerError = 'internal server error',
  Forbidden = 'Forbidden',
}

// code enums
export enum ErrorCode {
  NotFound = 404,
  InvalidParameter = 400,
  MissingParameter = 400,
  AuthenticationError = 401,
  Forbidden = 403,
  Conflict = 409,
  InternalServerError = 500,
}
