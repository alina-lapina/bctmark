'use strict';
const { Contract} = require('fabric-contract-api');

class testContract extends Contract {



   async queryMarks(ctx,studentId) {

    let marksAsBytes = await ctx.stub.getState(studentId);
    if (!marksAsBytes || marksAsBytes.toString().length <= 0) {
      throw new Error('Student with this Id does not exist: ');
       }
      let marks=JSON.parse(marksAsBytes.toString());

      return JSON.stringify(marks);
     }

   async addMarks(ctx,studentId,subject1,subject2,subject3) {

    let marks={
       subj1:subject1,
       subj2:subject2,
       subj3:subject3
       };

    await ctx.stub.putState(studentId,Buffer.from(JSON.stringify(marks)));

    console.log('Student Marks added To the ledger Succesfully..');

  }

   async deleteMarks(ctx,studentId) {


    await ctx.stub.deleteState(studentId);

    console.log('Student Marks deleted from the ledger Succesfully..');

    }

    async factorialOf(ctx, number) {
       let res = 1;
       for(let i = 2; i <= number; i++) {
           res = res * i;
       }

       res = JSON.stringify({
           result: res
       });
       await ctx.stub.putState("FACTORIAL", Buffer.from(res));
       return res;
    }

    async queryFactorial(ctx) {
        let resultAsBytes = await ctx.stub.getState("FACTORIAL");
        if (!resultAsBytes || resultAsBytes.toString().length <= 0) {
            throw new Error('No value set for FACTORIAL (maybe you forgot to call factorialOf(number)?)');
        }
        let result=JSON.parse(resultAsBytes.toString());

        return JSON.stringify(result);
    }

}

module.exports=testContract;
