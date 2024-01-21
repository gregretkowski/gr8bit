/*

Top level file for our system

*/

`include "../../verilog/src/fpga_leds.v"
`include "../../verilog/src/buttons.v"
`include "../../verilog/src/uart.v"
`include "../../verilog/src/clock.v"

`include "../../computer_fpga.v"

module top(
    input clk,
    input [5:0]led,
    input btn1,
    input btn2,
    input uartTx, // are these right or flipped??
    output uartRx 
);

    wire rset;
    wire full_clk = clk;
    wire cpu_clk;
    wire resetn; // not used.

    wire run;
    wire zro;
    wire [7:0] status;
    wire btn;

    clock #(1) clock(
        .CLK(full_clk),
        .RESET(rset),
        .clk(cpu_clk),
        .resetn(rsetn)
    );

    fpga_leds fpga_leds(
        .clk(cpu_clk),
        .run(run),
        .status(status),
        .zro(zro),
        .led(led)
    );

    buttons buttons(
        .clk(full_clk),
        .btn1(btn1),
        .btn2(btn2),
        .btn(btn),
        .reset(rset)
    );

endmodule